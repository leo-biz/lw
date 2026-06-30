#!/usr/bin/env python3
"""Unblock or partially resolve Markdown tasks whose task-ID dependencies are DONE.

Policy:
  wiki/07-systems/deterministic-automation.md   deterministic helper rules
  wiki/07-systems/file-claim-ledger.md           claim/release discipline
  wiki/07-systems/task-system.md                 task folder = status convention

Modes:
  Full scan   — inspect every open task with blocked_by dependencies (default)
  Targeted    — pass --completed <task-id> to scope to tasks that listed it as a blocker

Partial resolution:
  When a task has multiple blockers and some (but not all) are now DONE, those
  resolved deps are pruned from blocked_by in-place. The task stays in blocked/
  until its last blocker resolves, then moves to ready/.

  External blockers (strings that are not task IDs) and missing IDs are reported
  but never auto-resolved or pruned.

Usage:
  # Full scan — run after any task completes:
  python3 scripts/dependency_reconciliation.py

  # Targeted — scope to tasks blocked by a specific completed task:
  python3 scripts/dependency_reconciliation.py --completed task-2026-05-31-my-task

  # Dry-run — show what would change without touching files:
  python3 scripts/dependency_reconciliation.py --dry-run --verbose

  # Tests:
  python3 -m unittest scripts.tests.test_dependency_reconciliation -v
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORK_ROOT = VAULT_ROOT / "work"
LOCK_NAME = ".dependency-reconciliation.lock"
TASK_ID_RE = re.compile(r"^task-\d{4}-\d{2}-\d{2}-.+$")
OPEN_TASK_FOLDERS = ("inbox", "ready", "in-progress", "review", "blocked", "someday")


# ---------------------------------------------------------------------------
# Task I/O helpers (mirrors task_lease.py conventions)
# ---------------------------------------------------------------------------

def split_task(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path} has no YAML frontmatter")
    try:
        front_raw, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError(f"{path} has malformed YAML frontmatter") from exc
    return yaml.safe_load(front_raw) or {}, body


def task_text(metadata: dict, body: str) -> str:
    front = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    return f"---\n{front}\n---\n{body}"


def write_task(path: Path, metadata: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, suffix=".tmp") as tmp:
        tmp.write(task_text(metadata, body))
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


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


def move_task(src: Path, dest_dir: Path, metadata: dict, body: str) -> Path:
    dest = dest_dir / src.name
    if dest == src:
        write_task(src, metadata, body)
        return src
    write_task(dest, metadata, body)
    src.unlink()
    return dest


# ---------------------------------------------------------------------------
# Lock
# ---------------------------------------------------------------------------

@contextmanager
def reconciliation_lock(work_root: Path) -> Generator[None, None, None]:
    lock_path = work_root / LOCK_NAME
    try:
        lock_path.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(f"reconciliation already in progress: {lock_path}") from exc
    try:
        yield
    finally:
        shutil.rmtree(lock_path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Task index
# ---------------------------------------------------------------------------

def build_task_index(work_root: Path) -> dict[str, tuple[str, Path]]:
    """Return {task_id: (status, path)} for every Markdown task under work_root."""
    index: dict[str, tuple[str, Path]] = {}
    for subdir in work_root.iterdir():
        if not subdir.is_dir() or subdir.name.startswith("."):
            continue
        for md in subdir.glob("*.md"):
            try:
                meta, _ = split_task(md)
            except (ValueError, yaml.YAMLError):
                continue
            task_id = meta.get("id", "")
            status = meta.get("status", "")
            if task_id:
                index[task_id] = (status, md)
    return index


# ---------------------------------------------------------------------------
# blocked_by parsing
# ---------------------------------------------------------------------------

def parse_blocked_by(raw: object) -> list[str]:
    """Return a flat list of non-empty strings from a blocked_by value."""
    if not raw:
        return []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [str(raw).strip()]


def encode_blocked_by(deps: list[str]) -> object:
    """Encode a dep list back to a scalar or list for YAML storage."""
    if not deps:
        return ""
    return deps[0] if len(deps) == 1 else deps


def retain_depends_on(metadata: dict, deps: list[str]) -> bool:
    """Persist directional history for task-ID dependencies without duplicates."""
    retained = parse_blocked_by(metadata.get("depends_on"))
    for dep in deps:
        if TASK_ID_RE.match(dep) and dep not in retained:
            retained.append(dep)
    if retained:
        if metadata.get("depends_on") != retained:
            metadata["depends_on"] = retained
            return True
    return False


def sync_prerequisite_relationships(
    index: dict[str, tuple[str, Path]],
    dependent_id: str,
    deps: list[str],
    done_deps: list[str],
) -> None:
    """Mirror dependent history and active blocking state onto prerequisite tasks."""
    if not dependent_id:
        return
    for dep in deps:
        if not TASK_ID_RE.match(dep) or dep not in index:
            continue
        _, dep_path = index[dep]
        dep_meta, dep_body = split_task(dep_path)
        dependents = parse_blocked_by(dep_meta.get("dependents"))
        blocking = parse_blocked_by(dep_meta.get("blocking"))
        if dependent_id not in dependents:
            dependents.append(dependent_id)
        if dep in done_deps:
            blocking = [task_id for task_id in blocking if task_id != dependent_id]
        elif dependent_id not in blocking:
            blocking.append(dependent_id)
        if dep_meta.get("dependents") != dependents or dep_meta.get("blocking") != blocking:
            dep_meta["dependents"] = dependents
            dep_meta["blocking"] = blocking
            write_task(dep_path, dep_meta, dep_body)


def classify_dependency(dep: str, index: dict[str, tuple[str, Path]]) -> str:
    """Return 'done', 'pending', 'missing', or 'external'."""
    if not TASK_ID_RE.match(dep):
        return "external"
    if dep not in index:
        return "missing"
    status, _ = index[dep]
    return "done" if status == "DONE" else "pending"


# ---------------------------------------------------------------------------
# Reconciliation logic
# ---------------------------------------------------------------------------

class ReconcileResult:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.unblocked = False          # moved to ready/
        self.pruned = False             # resolved deps stripped from blocked_by in-place
        self.pruned_deps: list[str] = []
        self.dest: Path | None = None
        self.warnings: list[str] = []
        self.skipped_reason: str = ""


def reconcile_task(
    path: Path,
    index: dict[str, tuple[str, Path]],
    now: datetime,
    agent: str,
    dry_run: bool,
    completed_id: str | None = None,
) -> ReconcileResult:
    result = ReconcileResult(path)
    try:
        meta, body = split_task(path)
    except (ValueError, yaml.YAMLError) as exc:
        result.warnings.append(f"parse error: {exc}")
        result.skipped_reason = "parse error"
        return result

    raw = meta.get("blocked_by")
    deps = parse_blocked_by(raw)

    if not deps:
        result.skipped_reason = "no blocked_by dependencies"
        return result

    # Targeted mode: skip tasks that don't reference the completed task
    if completed_id and completed_id not in deps:
        result.skipped_reason = f"does not reference {completed_id}"
        return result

    classifications: dict[str, str] = {d: classify_dependency(d, index) for d in deps}

    for dep, cls in classifications.items():
        if cls == "external":
            result.warnings.append(f"external blocker (not auto-resolvable): {dep!r}")
        elif cls == "missing":
            result.warnings.append(f"task ID not found in work tree: {dep!r}")

    done_deps = [d for d, c in classifications.items() if c == "done"]
    remaining_deps = [d for d, c in classifications.items() if c != "done"]

    depends_on_changed = False
    if not dry_run:
        depends_on_changed = retain_depends_on(meta, deps)
        sync_prerequisite_relationships(index, meta.get("id", ""), deps, done_deps)

    if not remaining_deps:
        # Every dep is DONE → remove active gate and move blocked tasks to ready/.
        result.unblocked = True
        if not dry_run:
            if path.parent.name == "blocked":
                meta["status"] = "READY"
                meta["agent"] = "unassigned"
            meta.pop("blocked_by", None)
            msg = (
                "All blocking dependencies resolved (DONE). Moved to READY."
                if path.parent.name == "blocked"
                else "Removed resolved blocked_by dependencies from open task."
            )
            body = append_activity(body, now, agent, msg)
            dest_dir = path.parent.parent / "ready" if path.parent.name == "blocked" else path.parent
            result.dest = move_task(path, dest_dir, meta, body)

    elif done_deps:
        # Some deps resolved, some still pending → prune done deps in-place
        result.pruned = True
        result.pruned_deps = done_deps
        if not dry_run:
            meta["blocked_by"] = encode_blocked_by(remaining_deps)
            pruned_str = ", ".join(done_deps)
            remaining_str = ", ".join(remaining_deps)
            msg = f"Pruned resolved dep(s): {pruned_str}. Still waiting on: {remaining_str}."
            body = append_activity(body, now, agent, msg)
            write_task(path, meta, body)
    else:
        result.skipped_reason = f"unresolved deps: {remaining_deps}"
        if depends_on_changed:
            write_task(path, meta, body)

    return result


# ---------------------------------------------------------------------------
# Public entry point (callable from task_lease.py)
# ---------------------------------------------------------------------------

def reconcile_all(
    work_root: Path,
    completed_id: str | None = None,
    agent: str = "claude",
    dry_run: bool = False,
) -> list[ReconcileResult]:
    """Run reconciliation and return results. Caller handles output."""
    now = datetime.now(tz=timezone.utc).astimezone()

    with reconciliation_lock(work_root):
        index = build_task_index(work_root)
        tasks = sorted(
            path
            for folder in OPEN_TASK_FOLDERS
            for path in (work_root / folder).glob("*.md")
        )
        results = []
        for task_path in tasks:
            result = reconcile_task(task_path, index, now, agent, dry_run, completed_id)
            results.append(result)
    return results


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    work_root = args.work_root.resolve()
    if not work_root.is_dir():
        print("work/ does not exist — nothing to reconcile.")
        return 0

    results = reconcile_all(
        work_root,
        completed_id=args.completed or None,
        agent=args.agent,
        dry_run=args.dry_run,
    )

    if not results:
        print("No open tasks found.")
        return 0

    unblocked_count = 0
    pruned_count = 0
    warning_count = 0

    for result in results:
        for w in result.warnings:
            print(f"  WARN   {result.path.name}: {w}")
            warning_count += 1

        if result.unblocked:
            verb = "WOULD UNBLOCK" if args.dry_run else "UNBLOCKED"
            dest = result.dest or (work_root / "ready" / result.path.name)
            print(f"  {verb}  {result.path.name} -> {dest.relative_to(work_root)}")
            unblocked_count += 1
        elif result.pruned:
            verb = "WOULD PRUNE" if args.dry_run else "PRUNED"
            print(f"  {verb}    {result.path.name}: removed {result.pruned_deps}")
            pruned_count += 1
        elif result.skipped_reason and args.verbose:
            print(f"  SKIP   {result.path.name}: {result.skipped_reason}")

    suffix = " (dry run)" if args.dry_run else ""
    print(
        f"\nReconciled {len(results)} open task(s){suffix}: "
        f"{unblocked_count} unblocked, {pruned_count} pruned, {warning_count} warning(s)."
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unblock or prune Markdown tasks as their task-ID dependencies resolve.",
    )
    parser.add_argument(
        "--completed", metavar="TASK_ID",
        help="Scope to tasks blocked by this ID (e.g. after task_lease.py complete).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would change without modifying any files.",
    )
    parser.add_argument(
        "--agent", default="claude",
        help="Agent name written into activity entries (default: claude).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Also print skipped tasks and their reasons.",
    )
    parser.add_argument(
        "--work-root", type=Path, default=DEFAULT_WORK_ROOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> None:
    try:
        sys.exit(run(parse_args()))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
