#!/usr/bin/env python3
"""Report Git commits attributed to Markdown tasks through Task: trailers."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = VAULT_ROOT / "work"
ALIASES_FILE = VAULT_ROOT / "config" / "task-commit-aliases.yaml"
TASK_FOLDERS = ("inbox", "ready", "in-progress", "review", "blocked", "done", "someday")
HASH_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(root), *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "git command failed")
    return result.stdout.rstrip()


def task_ids(work_dir: Path) -> set[str]:
    ids = set()
    for folder in TASK_FOLDERS:
        for path in (work_dir / folder).glob("*.md"):
            text = path.read_text()
            if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                continue
            metadata = yaml.safe_load(text[4:].split("\n---\n", 1)[0]) or {}
            if metadata.get("id"):
                ids.add(str(metadata["id"]))
    return ids


def reviewed_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text()) or {}
    aliases = {}
    for alias, details in (payload.get("aliases") or {}).items():
        if isinstance(details, dict) and details.get("reviewed") is True and details.get("canonical_task"):
            aliases[str(alias)] = str(details["canonical_task"])
    return aliases


def resolve_task_id(task_id: str, work_dir: Path = WORK_DIR, aliases_file: Path = ALIASES_FILE) -> str:
    known = task_ids(work_dir)
    aliases = reviewed_aliases(aliases_file)
    canonical = aliases.get(task_id, task_id)
    if canonical not in known:
        raise ValueError(f"task ID does not resolve to a ledger file: {task_id}")
    return canonical


def commit_records(root: Path) -> list[dict]:
    output = run_git(
        root,
        "log",
        "--all",
        "--date=iso-strict",
        "--pretty=format:%H%x1f%s%x1f%aI%x1f%(trailers:key=Task,valueonly)%x1f%(trailers:key=Commit-Type,valueonly)%x1f%B%x1e",
    )
    records = []
    for raw in output.split("\x1e"):
        fields = raw.strip().split("\x1f")
        if len(fields) != 6:
            continue
        commit_hash, subject, author_date, task_value, commit_type, body = fields
        task_match = re.search(r"(?m)^Task:\s*(.+?)\s*$", body)
        type_match = re.search(r"(?m)^Commit-Type:\s*(.+?)\s*$", body)
        records.append(
            {
                "hash": commit_hash,
                "short_hash": commit_hash[:7],
                "subject": subject,
                "author_date": author_date,
                "task_id": task_value.strip() or (task_match.group(1) if task_match else ""),
                "commit_type": commit_type.strip() or (type_match.group(1) if type_match else "unknown"),
            }
        )
    return records


def commits_for_task(task_id: str, root: Path = VAULT_ROOT, work_dir: Path = WORK_DIR, aliases_file: Path = ALIASES_FILE) -> dict:
    canonical = resolve_task_id(task_id, work_dir, aliases_file)
    aliases = reviewed_aliases(aliases_file)
    accepted = {canonical, *(alias for alias, target in aliases.items() if target == canonical)}
    commits = []
    for record in commit_records(root):
        if record["task_id"] in accepted:
            record = {**record, "canonical_task_id": canonical}
            commits.append(record)
    return {"task_id": canonical, "aliases": sorted(accepted - {canonical}), "commits": commits}


def validate_ref(root: Path, ref: str) -> str:
    if not HASH_RE.fullmatch(ref):
        raise ValueError("commit ref must be a Git hash")
    return run_git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")


def commit_files(ref: str, root: Path = VAULT_ROOT) -> str:
    commit_hash = validate_ref(root, ref)
    return run_git(root, "show", "--stat", "--name-status", "--format=fuller", commit_hash)


def commit_diff(ref: str, root: Path = VAULT_ROOT) -> str:
    commit_hash = validate_ref(root, ref)
    return run_git(root, "show", "--format=fuller", "--find-renames", commit_hash)


def cumulative_diff(task_id: str, root: Path = VAULT_ROOT, work_dir: Path = WORK_DIR, aliases_file: Path = ALIASES_FILE) -> str:
    report = commits_for_task(task_id, root, work_dir, aliases_file)
    commits = list(reversed(report["commits"]))
    if not commits:
        return f"Task: {report['task_id']}\n\nNo attributed commits."
    oldest = commits[0]["hash"]
    newest = commits[-1]["hash"]
    parents = run_git(root, "rev-list", "--parents", "-n", "1", oldest).split()
    header = f"Task: {report['task_id']}\nCommits: {len(commits)}\nRange: {oldest[:7]}..{newest[:7]}\n\n"
    if len(parents) == 1:
        return header + run_git(root, "diff", "--find-renames", EMPTY_TREE, newest)
    return header + run_git(root, "diff", "--find-renames", parents[1], newest)


def audit(root: Path = VAULT_ROOT, work_dir: Path = WORK_DIR, aliases_file: Path = ALIASES_FILE) -> dict:
    known = task_ids(work_dir)
    aliases = reviewed_aliases(aliases_file)
    orphans = []
    unattributed = []
    for record in commit_records(root):
        task_id = record["task_id"]
        if not task_id:
            unattributed.append(record)
        elif aliases.get(task_id, task_id) not in known:
            orphans.append(record)
    return {
        "orphan_task_trailers": orphans,
        "unattributed_commits": unattributed,
        "heuristic_suggestions": [],
        "note": "Heuristic suggestions are report-only and require review before becoming aliases.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", nargs="?")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=VAULT_ROOT, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    try:
        payload = audit(root, root / "work", root / "config" / "task-commit-aliases.yaml") if args.audit else commits_for_task(
            args.task_id or "", root, root / "work", root / "config" / "task-commit-aliases.yaml"
        )
        if args.json or args.audit:
            print(json.dumps(payload, indent=2))
            return
        print(f"# Commits for {payload['task_id']}")
        for commit in payload["commits"]:
            print(f"{commit['short_hash']} | {commit['author_date']} | {commit['commit_type']} | {commit['subject']}")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
