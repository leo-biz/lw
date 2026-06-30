#!/usr/bin/env python3
"""Atomically claim, renew, release, reclaim, submit, or complete Markdown task leases.

Policy — read before modifying this file:
  wiki/07-systems/task-system.md               task lifecycle, folder=status, completed_at
  wiki/07-systems/file-claim-ledger.md         commit and lease closing conventions
  wiki/07-systems/multi-agent-coordination.md  lease semantics and session fields
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import yaml

try:
    from scripts.agent_presence_bridge import update_presence_best_effort
except ModuleNotFoundError:
    from agent_presence_bridge import update_presence_best_effort

VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORK_ROOT = VAULT_ROOT / "work"
PRESENCE_STATE = VAULT_ROOT / "runs" / "agent-presence.json"
LOCK_NAME = ".task-lease.lock"


def warn_if_presence_missing(session_id: str) -> None:
    if not PRESENCE_STATE.exists():
        print(
            "WARNING: no presence state found. "
            'Run scripts/agent_presence.py start --session-id "$SID" before claiming tasks.',
            file=sys.stderr,
        )
        return
    try:
        state = json.loads(PRESENCE_STATE.read_text())
    except (json.JSONDecodeError, OSError):
        return
    if session_id not in state:
        print(
            f"WARNING: session {session_id!r} not registered in presence ledger. "
            'Run scripts/agent_presence.py start --session-id "$SID" before claiming tasks.',
            file=sys.stderr,
        )


def now_local() -> datetime:
    return datetime.now().astimezone()


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_time(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def split_task(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path} has no YAML frontmatter")
    try:
        frontmatter, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError(f"{path} has malformed YAML frontmatter") from exc
    return yaml.safe_load(frontmatter) or {}, body


def task_text(metadata: dict, body: str) -> str:
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    return f"---\n{frontmatter}\n---\n{body.rstrip()}\n"


def append_activity(body: str, when: datetime, agent: str, message: str) -> str:
    marker = "## Activity"
    match = re.search(rf"(?m)^{re.escape(marker)}\s*$", body)
    if not match:
        raise ValueError("task is missing an ## Activity section")
    line = f"- {when.strftime('%Y-%m-%d %H:%M')} | {agent} | {message}"
    before = body[:match.start()]
    after = body[match.end():]
    next_heading = re.search(r"(?m)^## ", after)
    if next_heading:
        activity = after[:next_heading.start()]
        tail = "\n\n" + after[next_heading.start():].lstrip("\n")
    else:
        activity = after
        tail = ""
    return f"{before}{marker}{activity.rstrip()}\n\n{line}{tail}\n"


def require_complete_checklist(body: str) -> None:
    if re.search(r"(?m)^- \[ \] ", body):
        raise ValueError("all Definition of Done checklist items must be checked before submit or complete")


def require_review_proof(body: str) -> None:
    match = re.search(r"(?ms)^## Review Proof\n(.*?)(?=^## |\Z)", body)
    if not match:
        raise ValueError("task must include a ## Review Proof section before submit or complete")
    proof = match.group(1)
    missing = [
        heading
        for heading in ("### DoD Evidence", "### See It Work")
        if not re.search(rf"(?m)^{re.escape(heading)}\s*$", proof)
    ]
    if missing:
        raise ValueError(
            "task Review Proof is missing required subsection(s): "
            + ", ".join(missing)
        )


def write_task(path: Path, metadata: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as tmp:
        tmp.write(task_text(metadata, body))
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


@contextmanager
def task_lock(work_root: Path):
    lock_path = work_root / LOCK_NAME
    try:
        lock_path.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(f"lease update already in progress: {lock_path}") from exc
    try:
        yield
    finally:
        shutil.rmtree(lock_path)


def require_session(metadata: dict, session_id: str) -> None:
    if metadata.get("session_id") != session_id:
        raise ValueError("session_id does not own this task lease")


def move_task(path: Path, destination_dir: Path, metadata: dict, body: str) -> Path:
    destination = destination_dir / path.name
    if destination.exists() and destination != path:
        raise ValueError(f"destination already exists: {destination}")
    write_task(path, metadata, body)
    if destination != path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(path, destination)
    return destination


_TASK_ID_RE = re.compile(r"^task-\d{4}-\d{2}-\d{2}-(.+)$")


def resolve_task_path(task_arg: Path, work_root: Path, action: str) -> Path:
    """Return an absolute path to the task file.

    Accepts either a file path or a bare task ID (task-YYYY-MM-DD-slug).
    When an ID is given, derives the filename from the slug and probes the
    directory that action expects: work/ready/ for claim, work/in-progress/
    for all others.
    """
    resolved = task_arg.resolve()
    if resolved.exists():
        return resolved

    m = _TASK_ID_RE.match(task_arg.name)
    if m:
        slug = m.group(1)
        search_dir = work_root / ("ready" if action == "claim" else "in-progress")
        candidate = search_dir / f"{slug}.md"
        if candidate.exists():
            return candidate
        raise ValueError(
            f"no task file found for id '{task_arg}' in {search_dir}"
        )

    raise ValueError(f"task file not found: {task_arg}")


def apply_action(args: argparse.Namespace) -> Path:
    work_root = args.work_root.resolve()
    path = resolve_task_path(args.task, work_root, args.action)
    try:
        path.relative_to(work_root)
    except ValueError as exc:
        raise ValueError(f"task must be under {work_root}") from exc

    current_time = args.now or now_local()
    lease_until = current_time + timedelta(minutes=args.minutes)

    with task_lock(work_root):
        metadata, body = split_task(path)
        metadata["updated"] = current_time.date().isoformat()

        if args.action == "claim":
            warn_if_presence_missing(args.session_id)
            if metadata.get("status") != "READY" or path.parent != work_root / "ready":
                raise ValueError("claim requires a READY task in work/ready")
            metadata.update(
                status="IN_PROGRESS",
                agent=args.agent,
                claimed_at=iso_time(current_time),
                lease_until=iso_time(lease_until),
                session_id=args.session_id,
                last_activity=iso_time(current_time),
            )
            body = append_activity(body, current_time, args.agent, f"Claimed task with a {args.minutes}-minute lease.")
            return move_task(path, work_root / "in-progress", metadata, body)

        if metadata.get("status") != "IN_PROGRESS" or path.parent != work_root / "in-progress":
            raise ValueError(f"{args.action} requires an IN_PROGRESS task in work/in-progress")

        if args.action == "renew":
            require_session(metadata, args.session_id)
            metadata["lease_until"] = iso_time(lease_until)
            metadata["last_activity"] = iso_time(current_time)
            body = append_activity(body, current_time, args.agent, f"Renewed lease for {args.minutes} minutes.")
            dest = move_task(path, path.parent, metadata, body)
            update_presence_best_effort(
                "heartbeat",
                session_id=args.session_id,
                agent=args.agent,
                task_id=metadata.get("id", ""),
                current_slice=f"Renewed lease for {metadata.get('id', path.stem)}",
            )
            return dest

        if args.action == "release":
            require_session(metadata, args.session_id)
            metadata.update(status="READY", agent="unassigned", last_activity=iso_time(current_time))
            for key in ("claimed_at", "lease_until", "session_id"):
                metadata.pop(key, None)
            body = append_activity(body, current_time, args.agent, "Released task lease back to READY.")
            dest = move_task(path, work_root / "ready", metadata, body)
            update_presence_best_effort(
                "stop",
                session_id=args.session_id,
                agent=args.agent,
                task_id=metadata.get("id", ""),
                current_slice=f"Released task lease for {metadata.get('id', path.stem)}",
            )
            return dest

        if args.action == "submit":
            require_session(metadata, args.session_id)
            require_complete_checklist(body)
            require_review_proof(body)
            for key in ("claimed_at", "lease_until", "session_id"):
                metadata.pop(key, None)
            metadata.update(status="REVIEW", last_activity=iso_time(current_time))
            body = append_activity(body, current_time, args.agent, "Submitted for Leo review.")
            dest = move_task(path, work_root / "review", metadata, body)
            update_presence_best_effort(
                "wait",
                session_id=args.session_id,
                agent=args.agent,
                task_id=metadata.get("id", ""),
                current_slice=f"Submitted {metadata.get('id', path.stem)} for Leo review",
            )
            return dest

        if args.action == "complete":
            require_session(metadata, args.session_id)
            require_complete_checklist(body)
            require_review_proof(body)
            if metadata.get("leo_review_required"):
                raise ValueError(
                    "leo_review_required is set — use 'submit' to send this task to review first"
                )
            completed_task_id = metadata.get("id", "")
            for key in ("claimed_at", "lease_until", "session_id"):
                metadata.pop(key, None)
            metadata.update(
                status="DONE",
                completed_at=current_time.date().isoformat(),
                last_activity=iso_time(current_time),
            )
            body = append_activity(body, current_time, args.agent, "Marked task complete.")
            dest = move_task(path, work_root / "done", metadata, body)
            if completed_task_id:
                _reconcile_after_complete(completed_task_id, work_root, args.agent)
            return dest

        if args.action == "reclaim":
            existing_expiry = metadata.get("lease_until")
            if not existing_expiry:
                raise ValueError("cannot reclaim a task without lease_until")
            if parse_time(str(existing_expiry)) > current_time:
                raise ValueError("cannot reclaim an active lease")
            metadata.update(
                agent=args.agent,
                claimed_at=iso_time(current_time),
                lease_until=iso_time(lease_until),
                session_id=args.session_id,
                last_activity=iso_time(current_time),
            )
            body = append_activity(body, current_time, args.agent, f"Reclaimed expired lease for {args.minutes} minutes.")
            return move_task(path, path.parent, metadata, body)

        raise ValueError(f"unsupported action: {args.action}")


def _reconcile_after_complete(task_id: str, work_root: Path, agent: str) -> None:
    """Run targeted dependency reconciliation after a task is marked DONE. Non-fatal."""
    try:
        try:
            from scripts.dependency_reconciliation import reconcile_all
        except ModuleNotFoundError:
            from dependency_reconciliation import reconcile_all
        results = reconcile_all(work_root, completed_id=task_id, agent=agent)
        for r in results:
            if r.unblocked:
                name = r.dest.name if r.dest else r.path.name
                print(f"  ↳ unblocked: {name}")
            elif r.pruned:
                print(f"  ↳ pruned dep {task_id!r} from: {r.path.name}")
            for w in r.warnings:
                print(f"  ↳ warn: {r.path.name}: {w}", file=sys.stderr)
    except Exception as exc:
        print(f"WARNING: dependency reconciliation failed: {exc}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("claim", "renew", "release", "reclaim", "submit", "complete"))
    parser.add_argument("task", type=Path, help="Markdown task path")
    parser.add_argument("--agent", required=True, help="Worker name for ownership and activity")
    parser.add_argument("--session-id", required=True, help="Unique worker-session identifier")
    parser.add_argument("--minutes", type=int, default=120, help="Lease duration in minutes (default: 120)")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--now", type=parse_time, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.minutes < 1:
        parser.error("--minutes must be at least 1")
    return args


def main() -> None:
    try:
        destination = apply_action(parse_args())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(destination)


if __name__ == "__main__":
    main()
