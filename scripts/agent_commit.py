#!/usr/bin/env python3
"""Create an attributed agent checkpoint or completion commit from staged files.

Policy — read before modifying this file:
  wiki/07-systems/file-claim-ledger.md         checkpoint vs complete commit types, staging rules
  wiki/07-systems/multi-agent-coordination.md  attribution trailers and session fields
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from scripts.agent_presence_bridge import update_presence_best_effort
    from scripts.task_commit_report import resolve_task_id
except ModuleNotFoundError:
    from agent_presence_bridge import update_presence_best_effort
    from task_commit_report import resolve_task_id

VAULT_ROOT = Path(__file__).resolve().parent.parent


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


def staged_files(root: Path) -> list[str]:
    output = run_git(root, "diff", "--cached", "--name-only", "--no-renames", "--diff-filter=ACDMRTUXB")
    return [line for line in output.splitlines() if line]


def create_commit(args: argparse.Namespace) -> str:
    files = staged_files(args.root)
    if not files:
        raise ValueError("no staged files; stage the intended coherent slice explicitly")
    paths = list(getattr(args, "paths", []))
    if paths:
        missing = sorted(set(paths) - set(files))
        if missing:
            raise ValueError(f"--path must name staged files: {', '.join(missing)}")
        unstaged = run_git(args.root, "diff", "--name-only", "--", *paths)
        if unstaged:
            raise ValueError(
                "--path files have unstaged changes; restage or narrow the path scope: "
                + ", ".join(unstaged.splitlines())
            )

    allow_non_task = bool(getattr(args, "allow_non_task_attribution", False))
    if not allow_non_task:
        resolve_task_id(args.task_id, args.root / "work", args.root / "config" / "task-commit-aliases.yaml")

    trailers = [
        f"Agent: {args.agent}",
        f"Provider: {args.provider}",
        f"Session: {args.session_id}",
        f"Task: {args.task_id}",
        f"Commit-Type: {args.commit_type}",
    ]
    if args.session_url:
        trailers.append(f"Session-URL: {args.session_url}")

    command = ["commit", "-m", args.message]
    command.extend(("-m", "\n".join(trailers)))
    if paths:
        command.extend(("--only", "--", *paths))
    run_git(args.root, *command)
    commit = run_git(args.root, "log", "-1", "--pretty=format:%h")
    update_presence_best_effort(
        "checkpoint" if args.commit_type == "checkpoint" else "end",
        session_id=args.session_id,
        agent=args.agent,
        task_id=args.task_id,
        last_commit=commit,
        current_slice=f"Created {args.commit_type} commit {commit}",
    )
    return run_git(args.root, "log", "-1", "--pretty=format:%h %s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit_type", choices=("checkpoint", "complete"))
    parser.add_argument("--message", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--session-url", default="")
    parser.add_argument("--task-id", required=True)
    parser.add_argument(
        "--allow-non-task-attribution",
        action="store_true",
        help="Allow an explicit non-ledger Task trailer for administrative commits",
    )
    parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        default=[],
        help="Commit only this staged path; repeat to preserve unrelated staged files",
    )
    parser.add_argument("--root", type=Path, default=VAULT_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.root = args.root.resolve()
    return args


def main() -> None:
    try:
        print(create_commit(parse_args()))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
