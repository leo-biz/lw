#!/usr/bin/env python3
"""Declare live file ownership and annotate dirty Git files for local agents.

Policy — read before modifying this file:
  wiki/07-systems/file-claim-ledger.md         claim/release rules, OWNED/SHARED/EXPIRED/UNCLAIMED states
  wiki/07-systems/multi-agent-coordination.md  concurrent access model and session fields
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = VAULT_ROOT / "work" / ".file-claims.json"
DEFAULT_LOCK = VAULT_ROOT / "work" / ".file-claims.lock"


def now_local() -> datetime:
    return datetime.now().astimezone()


def iso_time(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@contextmanager
def ledger_lock(lock_path: Path):
    try:
        lock_path.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(f"file-claim update already in progress: {lock_path}") from exc
    try:
        yield
    finally:
        shutil.rmtree(lock_path)


def load_claims(path: Path) -> list[dict]:
    if not path.exists():
        return []
    value = json.loads(path.read_text())
    if not isinstance(value, list):
        raise ValueError(f"{path} must contain a JSON list")
    return value


def write_claims(path: Path, claims: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as tmp:
        json.dump(claims, tmp, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def normalize_path(root: Path, raw: str) -> str:
    path = Path(raw)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError(f"path must be inside {root}: {raw}") from exc
    normalized = path.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.rstrip("/")
    if not normalized or normalized.startswith("../"):
        raise ValueError(f"invalid claim path: {raw}")
    return normalized


def path_matches(claim_path: str, dirty_path: str) -> bool:
    return dirty_path == claim_path or dirty_path.startswith(f"{claim_path}/")


def git_status_tag(code: str) -> str:
    c = code.strip()
    if not c or c == "??":
        return "[NEW]"
    if "D" in c:
        return "[DELETED]"
    if "R" in c:
        return "[RENAMED]"
    if "A" in c:
        return "[ADDED]"
    return "[MODIFIED]"


def claims_overlap(first: str, second: str) -> bool:
    return path_matches(first, second) or path_matches(second, first)


def active_claims(claims: list[dict], now: datetime) -> list[dict]:
    return [claim for claim in claims if parse_time(claim["lease_until"]) > now]


def git_dirty(root: Path) -> list[tuple[str, str]]:
    result = subprocess.run(
        ("git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    dirty = []
    for line in result.stdout.splitlines():
        status, path = line[:2], line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        dirty.append((status, path))
    return dirty


def claim_paths(args: argparse.Namespace) -> None:
    now = args.now or now_local()
    lease_until = now + timedelta(minutes=args.minutes)
    requested = [normalize_path(args.root, raw) for raw in args.paths]
    with ledger_lock(args.lock):
        claims = active_claims(load_claims(args.ledger), now)
        for path in requested:
            for existing in claims:
                if existing["session_id"] == args.session_id:
                    continue
                if claims_overlap(path, existing["path"]) and not args.allow_shared:
                    raise ValueError(
                        f"{path} overlaps active claim {existing['path']} "
                        f"owned by {existing['agent']} ({existing['session_id']})"
                    )
            claims = [
                existing
                for existing in claims
                if not (existing["session_id"] == args.session_id and existing["path"] == path)
            ]
            claims.append(
                {
                    "path": path,
                    "agent": args.agent,
                    "provider": args.provider,
                    "session_id": args.session_id,
                    "session_url": args.session_url,
                    "task_id": args.task_id,
                    "claimed_at": iso_time(now),
                    "lease_until": iso_time(lease_until),
                    "shared": args.allow_shared,
                }
            )
        write_claims(args.ledger, claims)
    for path in requested:
        print(f"CLAIMED {path} | {args.agent} | until {iso_time(lease_until)}")


def release_paths(args: argparse.Namespace) -> None:
    requested = {normalize_path(args.root, raw) for raw in args.paths}
    with ledger_lock(args.lock):
        claims = load_claims(args.ledger)
        kept = []
        released = []
        for claim in claims:
            owned = claim["session_id"] == args.session_id
            selected = not requested or claim["path"] in requested
            if owned and selected:
                released.append(claim)
            else:
                kept.append(claim)
        write_claims(args.ledger, kept)
    for claim in released:
        print(f"RELEASED {claim['path']} | {claim['agent']}")
    if not released:
        print("No matching claims.")


def prune_claims(args: argparse.Namespace) -> None:
    now = args.now or now_local()
    with ledger_lock(args.lock):
        claims = load_claims(args.ledger)
        active = active_claims(claims, now)
        write_claims(args.ledger, active)
    print(f"PRUNED {len(claims) - len(active)} expired claim(s).")


def _owners_str(claims: list[dict], include_task: bool = True) -> str:
    parts = []
    for claim in claims:
        s = f"{claim['agent']}@{claim.get('provider') or 'unknown'}:{claim['session_id']}"
        if include_task and claim.get("task_id"):
            s += f" task={claim['task_id']}"
        if claim.get("session_url"):
            s += f" url={claim['session_url']}"
        parts.append(s)
    return ", ".join(parts)


def show_status(args: argparse.Namespace) -> None:
    now = args.now or now_local()
    claims = load_claims(args.ledger)
    use_json = getattr(args, "json", False)

    rows = []
    for git_code, path in git_dirty(args.root):
        matches = [claim for claim in claims if path_matches(claim["path"], path)]
        active = [claim for claim in matches if parse_time(claim["lease_until"]) > now]
        if active:
            label = "SHARED" if len(active) > 1 or any(claim.get("shared") for claim in active) else "OWNED"
            owners = _owners_str(active)
        elif matches:
            label = "EXPIRED"
            owners = _owners_str(matches, include_task=False)
        else:
            label = "UNCLAIMED"
            owners = f"python3 scripts/file_claims.py claim {path} --agent <agent> --session-id <SID>"
        rows.append({"git_code": git_code.strip(), "path": path, "label": label, "owners": owners})

    if use_json:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return

    for row in rows:
        tag = git_status_tag(row["git_code"])
        print(f"{tag:<12} {row['path']} | {row['label']} | {row['owners']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=VAULT_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER, help=argparse.SUPPRESS)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK, help=argparse.SUPPRESS)
    parser.add_argument("--now", type=parse_time, help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="action", required=True)

    claim = subparsers.add_parser("claim", help="Claim files or directories before editing")
    claim.add_argument("paths", nargs="+")
    claim.add_argument("--agent", required=True)
    claim.add_argument("--provider", default="")
    claim.add_argument("--session-id", required=True)
    claim.add_argument("--session-url", default="")
    claim.add_argument("--task-id", default="")
    claim.add_argument("--minutes", type=int, default=120)
    claim.add_argument("--allow-shared", action="store_true")
    claim.set_defaults(run=claim_paths)

    release = subparsers.add_parser("release", help="Release this session's claims")
    release.add_argument("paths", nargs="*")
    release.add_argument("--session-id", required=True)
    release.set_defaults(run=release_paths)

    prune = subparsers.add_parser("prune", help="Remove expired claims")
    prune.set_defaults(run=prune_claims)

    status = subparsers.add_parser("status", help="Annotate dirty Git files with live ownership")
    status.add_argument("--json", action="store_true", help="Output JSON array")
    status.set_defaults(run=show_status)

    args = parser.parse_args()
    args.root = args.root.resolve()
    args.ledger = args.ledger.resolve()
    args.lock = args.lock.resolve()
    if getattr(args, "minutes", 1) < 1:
        parser.error("--minutes must be at least 1")
    return args


def main() -> None:
    try:
        args = parse_args()
        args.run(args)
    except (json.JSONDecodeError, OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
