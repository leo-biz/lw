#!/usr/bin/env python3
"""Report Markdown task lifecycle and dependency invariant violations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = VAULT_ROOT / "work"
FOLDER_STATUS = {
    "inbox": "INBOX", "ready": "READY", "in-progress": "IN_PROGRESS",
    "review": "REVIEW", "blocked": "BLOCKED", "done": "DONE", "someday": "SOMEDAY",
}
TASK_ID_RE = re.compile(r"^task-\d{4}-\d{2}-\d{2}-.+$")


def values(raw: object) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item)]
    return [str(raw)]


def unchecked_items(body: str) -> list[str]:
    match = re.search(r"(?ms)^## Definition of Done\n(.*?)(?=^## |\Z)", body)
    return re.findall(r"(?m)^- \[ \] (.+)$", match.group(1) if match else "")


def load_tasks(work_dir: Path) -> list[dict]:
    tasks = []
    for folder, expected in FOLDER_STATUS.items():
        for path in sorted((work_dir / folder).glob("*.md")):
            try:
                text = path.read_text()
                frontmatter, body = text[4:].split("\n---\n", 1)
                metadata = yaml.safe_load(frontmatter) or {}
            except (OSError, ValueError, yaml.YAMLError) as exc:
                tasks.append({"path": path, "folder": folder, "expected": expected, "error": str(exc), "metadata": {}, "body": ""})
                continue
            tasks.append({"path": path, "folder": folder, "expected": expected, "metadata": metadata, "body": body})
    return tasks


def validate(work_dir: Path = WORK_DIR) -> list[dict]:
    tasks = load_tasks(work_dir)
    findings = []

    def add(code: str, task: dict, message: str) -> None:
        findings.append({"code": code, "path": str(task["path"].relative_to(work_dir.parent)), "message": message})

    ids: dict[str, list[dict]] = defaultdict(list)
    for task in tasks:
        metadata = task["metadata"]
        if task.get("error"):
            add("PARSE_ERROR", task, task["error"])
            continue
        task_id = str(metadata.get("id") or "")
        if task_id:
            ids[task_id].append(task)
        status = str(metadata.get("status") or "")
        if status != task["expected"]:
            add("FOLDER_STATUS_MISMATCH", task, f"folder expects {task['expected']}, found {status or '(missing)'}")
        unchecked = unchecked_items(task["body"])
        if status == "IN_PROGRESS":
            missing = [key for key in ("session_id", "lease_until") if not metadata.get(key)]
            if not metadata.get("agent") or metadata.get("agent") == "unassigned":
                missing.append("agent")
            if missing:
                add("IN_PROGRESS_LEASE_MISSING", task, f"missing active ownership fields: {', '.join(missing)}")
        else:
            stale = [key for key in ("claimed_at", "lease_until", "session_id") if metadata.get(key)]
            if stale:
                add("NON_ACTIVE_LEASE_METADATA", task, f"non-IN_PROGRESS task retains: {', '.join(stale)}")
        if status == "REVIEW" and unchecked:
            add("REVIEW_UNCHECKED_DOD", task, f"{len(unchecked)} unchecked Definition of Done item(s)")
        if status == "DONE":
            if unchecked:
                add("DONE_UNCHECKED_DOD", task, f"{len(unchecked)} unchecked Definition of Done item(s)")
            if not metadata.get("completed_at"):
                add("DONE_MISSING_COMPLETED_AT", task, "DONE task is missing completed_at")
    for task_id, matches in ids.items():
        if len(matches) > 1:
            for task in matches:
                add("DUPLICATE_TASK_ID", task, f"duplicate task ID: {task_id}")

    index = {task_id: matches[0] for task_id, matches in ids.items()}
    done_ids = {task_id for task_id, task in index.items() if task["metadata"].get("status") == "DONE"}
    for dependent_id, task in index.items():
        metadata = task["metadata"]
        for dependency_id in values(metadata.get("blocked_by")):
            if dependency_id in done_ids:
                add("STALE_COMPLETED_BLOCKER", task, f"blocked_by retains completed task: {dependency_id}")
            prerequisite = index.get(dependency_id)
            if prerequisite and dependent_id not in values(prerequisite["metadata"].get("blocking")):
                add("MISSING_RECIPROCAL_BLOCKING", task, f"{dependency_id} lacks blocking: {dependent_id}")
        for dependency_id in values(metadata.get("depends_on")):
            prerequisite = index.get(dependency_id)
            if prerequisite and dependent_id not in values(prerequisite["metadata"].get("dependents")):
                add("MISSING_RECIPROCAL_DEPENDENT", task, f"{dependency_id} lacks dependents: {dependent_id}")
        for link in re.findall(r"(?m)^- related_to: \[\[(.+?)\]\]", task["body"]):
            linked = Path(link.split("|", 1)[0]).stem
            for dependency_id in values(metadata.get("depends_on")):
                if linked == dependency_id.removeprefix("task-") or linked in dependency_id:
                    add("NONDIRECTIONAL_DEPENDENCY_LINK", task, f"related_to should be depends_on for: {dependency_id}")
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--work-root", type=Path, default=WORK_DIR, help=argparse.SUPPRESS)
    args = parser.parse_args()
    findings = validate(args.work_root.resolve())
    if args.json:
        print(json.dumps({"findings": findings, "count": len(findings)}, indent=2))
    else:
        for finding in findings:
            print(f"{finding['code']}: {finding['path']}: {finding['message']}")
        print(f"\nTask lifecycle validator: {len(findings)} finding(s).")
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
