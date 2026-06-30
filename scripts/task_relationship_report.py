#!/usr/bin/env python3
"""Compact per-task relationship discovery report for fresh-thread work packets.

Shows explicit relationships (blocked_by, depends_on, blocking, dependents, related_tasks, parent_task, supersedes),
reverse-blocking tasks, and scored suggestions based on shared signals.
Report-only — never infers blocked_by, merges tasks, or assigns workers.

Policy:
  wiki/07-systems/multi-agent-coordination.md  task relationship semantics
  wiki/07-systems/task-system.md               task folder = status convention

Usage:
  # Report for a specific task (path or bare ID):
  python3 scripts/task_relationship_report.py work/ready/my-task.md
  python3 scripts/task_relationship_report.py task-2026-05-31-my-task

  # Compact format suitable for a work packet:
  python3 scripts/task_relationship_report.py task-2026-05-31-my-task --compact

  # Tests:
  python3 -m unittest scripts.tests.test_task_relationship_report -v

Relationship semantics:
  blocked_by      This task cannot start until all listed tasks are DONE.
  depends_on      Durable directional dependency history, including DONE tasks.
  blocking        Active inverse of blocked_by — unresolved tasks waiting on this one.
  dependents      Durable inverse of depends_on — tasks that require this one.
  related_tasks   Explicitly related; shared context or workstream.
  parent_task     This task is a subtask of the listed task.
  supersedes      This task replaces the listed task.
  blocks          Reverse of blocked_by — tasks waiting on this one.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORK_ROOT = VAULT_ROOT / "work"
TASK_ID_RE = re.compile(r"^task-\d{4}-\d{2}-\d{2}-.+$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]+)?\]\]")
_STOP_WORDS = frozenset(
    "a an the and or to for of in on at by with from as is are was were be been "
    "have has had do does did will would could should may might must shall can "
    "add build create update fix remove get set run list show report generate "
    "task work help this that these those".split()
)


# ---------------------------------------------------------------------------
# Task I/O (mirrors dependency_reconciliation.py)
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


def resolve_task_path(task_arg: Path, work_root: Path) -> Path:
    """Accept a file path or bare task ID, return the resolved Path."""
    resolved = task_arg.resolve()
    if resolved.exists():
        return resolved
    # Try bare task ID
    m = TASK_ID_RE.match(task_arg.name)
    if m:
        slug = re.sub(r"^task-\d{4}-\d{2}-\d{2}-", "", task_arg.name)
        filename = f"{slug}.md"
        for subdir in work_root.iterdir():
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            candidate = subdir / filename
            if candidate.exists():
                return candidate
    raise FileNotFoundError(f"cannot find task: {task_arg}")


# ---------------------------------------------------------------------------
# Task index
# ---------------------------------------------------------------------------

class TaskRecord(NamedTuple):
    task_id: str
    status: str
    path: Path
    meta: dict
    body: str


def build_index(work_root: Path) -> dict[str, TaskRecord]:
    index: dict[str, TaskRecord] = {}
    for subdir in work_root.iterdir():
        if not subdir.is_dir() or subdir.name.startswith("."):
            continue
        for md in subdir.glob("*.md"):
            try:
                meta, body = split_task(md)
            except (ValueError, yaml.YAMLError):
                continue
            task_id = meta.get("id", "")
            if task_id:
                index[task_id] = TaskRecord(
                    task_id=task_id,
                    status=meta.get("status", ""),
                    path=md,
                    meta=meta,
                    body=body,
                )
    return index


# ---------------------------------------------------------------------------
# Explicit relationship helpers
# ---------------------------------------------------------------------------

def _as_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()]


def explicit_relationships(meta: dict) -> dict[str, list[str]]:
    return {
        "blocked_by": _as_list(meta.get("blocked_by")),
        "depends_on": _as_list(meta.get("depends_on")),
        "blocking": _as_list(meta.get("blocking")),
        "dependents": _as_list(meta.get("dependents")),
        "related_tasks": _as_list(meta.get("related_tasks")),
        "parent_task": _as_list(meta.get("parent_task")),
        "supersedes": _as_list(meta.get("supersedes")),
    }


def reverse_blocks(target_id: str, index: dict[str, TaskRecord]) -> list[str]:
    """Return IDs of tasks that list target_id in their blocked_by."""
    blocked = []
    for rec in index.values():
        if rec.task_id == target_id:
            continue
        if target_id in _as_list(rec.meta.get("blocked_by")):
            blocked.append(rec.task_id)
    return blocked


# ---------------------------------------------------------------------------
# Scoring: suggested related tasks
# ---------------------------------------------------------------------------

class Suggestion(NamedTuple):
    task_id: str
    score: int
    reasons: list[str]
    status: str
    title: str


def _extract_wikilinks(text: str) -> set[str]:
    return {m.strip().lower() for m in WIKILINK_RE.findall(text)}


def _title_words(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}


def score_candidate(target: TaskRecord, candidate: TaskRecord) -> Suggestion | None:
    if candidate.task_id == target.task_id:
        return None

    # Already explicitly related — skip (reported in explicit section)
    explicit = explicit_relationships(target.meta)
    all_explicit = set(
        explicit["blocked_by"]
        + explicit["depends_on"]
        + explicit["blocking"]
        + explicit["dependents"]
        + explicit["related_tasks"]
        + explicit["parent_task"]
        + explicit["supersedes"]
    )
    if candidate.task_id in all_explicit:
        return None

    score = 0
    reasons: list[str] = []
    t_meta, c_meta = target.meta, candidate.meta

    # Same parent task
    if t_meta.get("parent_task") and t_meta.get("parent_task") == c_meta.get("parent_task"):
        score += 3
        reasons.append(f"same parent_task: {t_meta['parent_task']}")

    # Same workstream
    if t_meta.get("workstream") and t_meta.get("workstream") == c_meta.get("workstream"):
        score += 2
        reasons.append(f"same workstream: {t_meta['workstream']}")

    # Shared wiki_page
    t_wiki = set(_as_list(t_meta.get("wiki_page")))
    c_wiki = set(_as_list(c_meta.get("wiki_page")))
    shared_wiki = t_wiki & c_wiki
    if shared_wiki:
        score += 3 * len(shared_wiki)
        reasons.append(f"shared wiki_page: {', '.join(sorted(shared_wiki))}")

    # Shared source
    t_src = set(_as_list(t_meta.get("source")))
    c_src = set(_as_list(c_meta.get("source")))
    shared_src = t_src & c_src
    if shared_src:
        score += 2 * len(shared_src)
        reasons.append(f"shared source: {', '.join(sorted(shared_src))}")

    # Shared repo
    if t_meta.get("repo") and t_meta.get("repo") == c_meta.get("repo"):
        score += 2
        reasons.append(f"same repo: {t_meta['repo']}")

    # Shared tags
    t_tags = set(t_meta.get("tags") or [])
    c_tags = set(c_meta.get("tags") or [])
    shared_tags = t_tags & c_tags
    if shared_tags:
        score += len(shared_tags)
        reasons.append(f"shared tags: {', '.join(sorted(shared_tags))}")

    # Shared wikilinks in body
    t_links = _extract_wikilinks(target.body)
    c_links = _extract_wikilinks(candidate.body)
    shared_links = t_links & c_links
    if shared_links:
        score += len(shared_links)
        reasons.append(f"shared wikilinks: {', '.join(sorted(shared_links)[:3])}")

    # Title word overlap
    t_words = _title_words(t_meta.get("title", ""))
    c_words = _title_words(c_meta.get("title", ""))
    shared_words = t_words & c_words
    if shared_words:
        score += len(shared_words)
        reasons.append(f"title overlap: {', '.join(sorted(shared_words))}")

    if score == 0:
        return None
    return Suggestion(
        task_id=candidate.task_id,
        score=score,
        reasons=reasons,
        status=candidate.status,
        title=candidate.meta.get("title", ""),
    )


def suggest_related(target: TaskRecord, index: dict[str, TaskRecord], top_n: int = 8) -> list[Suggestion]:
    suggestions = []
    for candidate in index.values():
        s = score_candidate(target, candidate)
        if s is not None:
            suggestions.append(s)
    return sorted(suggestions, key=lambda s: (-s.score, s.task_id))[:top_n]


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _status_tag(status: str) -> str:
    return {
        "DONE": "[DONE]",
        "READY": "[READY]",
        "IN_PROGRESS": "[IN_PROGRESS]",
        "BLOCKED": "[BLOCKED]",
        "REVIEW": "[REVIEW]",
    }.get(status, f"[{status}]")


def render_report(target: TaskRecord, index: dict[str, TaskRecord], compact: bool = False) -> str:
    lines: list[str] = []
    meta = target.meta
    rel = explicit_relationships(meta)
    blocks = reverse_blocks(target.task_id, index)
    suggestions = suggest_related(target, index)

    title = meta.get("title", target.task_id)
    status = _status_tag(target.status)
    lines.append(f"# {title}")
    lines.append(f"  id:     {target.task_id}")
    try:
        display_path = target.path.relative_to(VAULT_ROOT)
    except ValueError:
        display_path = target.path
    lines.append(f"  status: {status}  path: {display_path}")

    # Explicit relationships
    lines.append("")
    lines.append("## Explicit Relationships")

    def _fmt_ids(ids: list[str], label: str) -> None:
        if not ids:
            return
        lines.append(f"  {label}:")
        for tid in ids:
            rec = index.get(tid)
            if rec:
                lines.append(f"    {_status_tag(rec.status)} {tid}  — {rec.meta.get('title', '')}")
            else:
                lines.append(f"    [UNKNOWN] {tid}")

    _fmt_ids(rel["blocked_by"], "blocked_by")
    _fmt_ids(rel["depends_on"], "depends_on")
    _fmt_ids(rel["blocking"], "blocking")
    _fmt_ids(rel["dependents"], "dependents")
    _fmt_ids(rel["related_tasks"], "related_tasks")
    _fmt_ids(rel["parent_task"], "parent_task")
    _fmt_ids(rel["supersedes"], "supersedes")
    _fmt_ids(blocks, "blocks (reverse)")

    if not any([rel["blocked_by"], rel["depends_on"], rel["blocking"], rel["dependents"], rel["related_tasks"], rel["parent_task"], rel["supersedes"], blocks]):
        lines.append("  (none)")

    # Suggested
    lines.append("")
    lines.append("## Suggested Related Tasks")
    if not suggestions:
        lines.append("  (none)")
    else:
        for s in suggestions:
            lines.append(f"  score={s.score:2d}  {_status_tag(s.status)} {s.task_id}")
            lines.append(f"         {s.title}")
            if not compact:
                for r in s.reasons:
                    lines.append(f"           · {r}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task", type=Path, help="Task file path or bare task ID.")
    parser.add_argument(
        "--compact", action="store_true",
        help="Omit per-suggestion reason lines (suitable for work packets).",
    )
    parser.add_argument(
        "--top", type=int, default=8, metavar="N",
        help="Max suggested tasks to show (default: 8).",
    )
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    work_root = args.work_root.resolve()
    try:
        path = resolve_task_path(args.task, work_root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

    try:
        meta, body = split_task(path)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

    index = build_index(work_root)
    task_id = meta.get("id", "")
    if not task_id:
        print(f"ERROR: task has no id field: {path}", file=sys.stderr)
        raise SystemExit(1)

    target = TaskRecord(
        task_id=task_id,
        status=meta.get("status", ""),
        path=path,
        meta=meta,
        body=body,
    )
    print(render_report(target, index, compact=args.compact))


if __name__ == "__main__":
    main()
