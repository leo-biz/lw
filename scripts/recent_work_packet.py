#!/usr/bin/env python3
"""Print a compact, report-only takeover packet for a fresh agent session.

Policy — read before modifying this file:
  wiki/07-systems/recent-work-takeover-packet.md  packet format and required fields
  wiki/07-systems/task-system.md                  task folder structure and frontmatter schema
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
ACTIVE_FOLDERS = ("in-progress", "review", "blocked")


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(root), *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.rstrip()


def split_task(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path} has no YAML frontmatter")
    frontmatter, body = text[4:].split("\n---\n", 1)
    return yaml.safe_load(frontmatter) or {}, body


def recent_activity(body: str, limit: int) -> list[str]:
    if "## Activity" not in body:
        return []
    activity = body.split("## Activity", 1)[1].split("\n## ", 1)[0]
    lines = [line.strip() for line in activity.splitlines() if line.startswith("- ")]
    return lines[-limit:]


def task_summary(root: Path, path: Path, activity_lines: int) -> list[str]:
    metadata, body = split_task(path)
    relative = path.relative_to(root)
    title = metadata.get("title") or path.stem
    status = metadata.get("status") or path.parent.name.upper()
    lines = [f"- `{relative}` | {status} | {title}"]
    details = []
    for key in ("agent", "last_activity", "lease_until", "blocked_by"):
        value = metadata.get(key)
        if value:
            details.append(f"{key}: {value}")
    if details:
        lines.append(f"  - {'; '.join(details)}")
    checkpoint = metadata.get("handoff_checkpoint")
    if checkpoint:
        lines.append(f"  - checkpoint: {checkpoint}")
    for line in recent_activity(body, activity_lines):
        lines.append(f"  {line}")
    return lines


def task_files(work_root: Path, folders: tuple[str, ...]) -> list[Path]:
    files = []
    for folder in folders:
        files.extend(sorted((work_root / folder).glob("*.md")))
    return files


def recent_done_tasks(root: Path, work_root: Path, limit: int) -> list[str]:
    paths = task_files(work_root, ("done",))
    paths.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    lines = []
    for path in paths[:limit]:
        metadata, _ = split_task(path)
        title = metadata.get("title") or path.stem
        updated = metadata.get("updated") or "unknown-date"
        lines.append(f"- `{path.relative_to(root)}` | updated {updated} | {title}")
    return lines


def section(title: str, lines: list[str], empty: str = "- None") -> str:
    return f"## {title}\n" + "\n".join(lines or [empty])


def build_packet(args: argparse.Namespace) -> str:
    root = args.root.resolve()
    work_root = root / "work"
    status = run_git(root, "status", "--short").splitlines()
    commits = run_git(
        root,
        "log",
        f"--since={args.since}",
        f"--max-count={args.max_commits}",
        "--date=short",
        "--pretty=format:- `%h` | %ad | %s",
    ).splitlines()
    active = []
    for path in task_files(work_root, ACTIVE_FOLDERS):
        active.extend(task_summary(root, path, args.activity_lines))
    done = recent_done_tasks(root, work_root, args.max_done)

    sections = [
        "# Recent Work Takeover Packet",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "Use this as a retrieval map, not as permission to bulk-read the vault. "
        "Start with the relevant active task, its checkpoint, and the smallest useful diff.",
        "",
        section("Dirty Worktree", [f"- `{line}`" for line in status]),
        "",
        section("Recent Commits", commits),
        "",
        section("Active Task Packets", active),
        "",
        section("Recently Done Tasks", done),
        "",
        "## Fresh-Agent Sequence",
        "1. Read `AGENTS.md`, propose the correct mode, and wait for Leo's confirmation.",
        "2. Read the one active task relevant to the request and its linked context only as needed.",
        "3. Inspect `git status --short`; inspect diffs only for files relevant to the resumed slice.",
        "4. Preserve unrelated dirty files. Do not infer ownership from this report alone.",
        "5. Before stopping, update the task checkpoint and Activity with durable continuation state.",
    ]
    return "\n".join(sections) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=VAULT_ROOT, help="Vault root")
    parser.add_argument("--since", default="3 days ago", help="Git --since value")
    parser.add_argument("--max-commits", type=int, default=8)
    parser.add_argument("--max-done", type=int, default=6)
    parser.add_argument("--activity-lines", type=int, default=3)
    args = parser.parse_args()
    for key in ("max_commits", "max_done", "activity_lines"):
        if getattr(args, key) < 1:
            parser.error(f"--{key.replace('_', '-')} must be at least 1")
    return args


def main() -> None:
    try:
        print(build_packet(parse_args()), end="")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
