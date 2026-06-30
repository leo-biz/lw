#!/usr/bin/env python3
"""Rank eligible READY tasks, print a compact packet, and optionally claim one."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

try:
    from scripts.dependency_reconciliation import parse_blocked_by, reconcile_all
    from scripts.task_lease import apply_action
    from scripts.task_relationship_report import (
        TaskRecord, build_index, render_report, resolve_task_path, split_task,
    )
except ModuleNotFoundError:  # Direct execution from scripts/.
    from dependency_reconciliation import parse_blocked_by, reconcile_all
    from task_lease import apply_action
    from task_relationship_report import (
        TaskRecord, build_index, render_report, resolve_task_path, split_task,
    )

VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORK_ROOT = VAULT_ROOT / "work"
PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}
EFFORT_ORDER = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4}
RECENT_COLUMNS = {
    "inbox": "INBOX",
    "ready": "READY",
    "in-progress": "IN_PROGRESS",
    "review": "REVIEW",
    "blocked": "BLOCKED",
    "done": "DONE",
    "someday": "SOMEDAY",
}


@dataclass(frozen=True)
class Candidate:
    path: Path
    meta: dict
    body: str
    rank: tuple
    reasons: tuple[str, ...]

    @property
    def task_id(self) -> str:
        return str(self.meta.get("id", self.path.stem))


def parse_date(value: object, fallback: date) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return fallback


def file_created_date(path: Path) -> date:
    stat = path.stat()
    timestamp = getattr(stat, "st_birthtime", stat.st_mtime)
    return date.fromtimestamp(timestamp)


def task_created_date(meta: dict, path: Path) -> date:
    return parse_date(meta.get("created"), file_created_date(path))


def quadrant_bucket(meta: dict) -> int:
    quadrant = str(meta.get("quadrant", "Q2"))
    priority = str(meta.get("priority", "P2"))
    if quadrant == "Q1" and priority == "P1":
        return 0
    if quadrant == "Q2" and priority == "P1":
        return 1
    return {"Q1": 2, "Q2": 3, "Q3": 4, "Q4": 5}.get(quadrant, 6)


def rank_task(path: Path, meta: dict, body: str) -> Candidate:
    priority = str(meta.get("priority", "P2"))
    effort = str(meta.get("ai_effort", ""))
    due = parse_date(meta.get("due"), date.max)
    created = parse_date(meta.get("created"), date.max)
    reasons = [f"{meta.get('quadrant', 'Q2')} {priority}", f"ai_effort={effort or 'unknown'}"]
    if due != date.max:
        reasons.append(f"due={due.isoformat()}")
    if effort == "XL":
        reasons.append("decompose XL work before execution")
    return Candidate(
        path, meta, body,
        (
            quadrant_bucket(meta), PRIORITY_ORDER.get(priority, 9), due, created,
            EFFORT_ORDER.get(effort, 9), str(meta.get("id", path.stem)),
        ),
        tuple(reasons),
    )


def eligible_candidates(work_root: Path, include_review: bool = False) -> list[Candidate]:
    candidates = []
    for path in sorted((work_root / "ready").glob("*.md")):
        meta, body = split_task(path)
        if meta.get("status") != "READY" or parse_blocked_by(meta.get("blocked_by")):
            continue
        if meta.get("leo_review_required") and not include_review:
            continue
        candidates.append(rank_task(path, meta, body))
    return sorted(candidates, key=lambda candidate: candidate.rank)


def recent_activity(body: str, limit: int = 3) -> list[str]:
    if "## Activity" not in body:
        return []
    section = body.split("## Activity", 1)[1].split("\n## ", 1)[0]
    return [line for line in section.splitlines() if line.startswith("- ")][-limit:]


def definition_of_done(body: str) -> list[str]:
    return [line for line in body.splitlines() if line.startswith("- [")]


def required_policy_links(meta: dict) -> list[str]:
    """Return only task-surface policies not already covered by bootstrap."""
    text = " ".join(str(meta.get(key, "")) for key in (
        "title", "source", "wiki_page", "workstream", "tags",
    )).lower()
    links = []
    for markers, link in (
        (("raw/inbox", "inbox-routing"), "[[inbox-routing-workflow]]"),
        (("youtube", "transcript"), "[[youtube-transcript-workflow]]"),
        (("learning", "synthesis"), "[[learning-to-application-loop]]"),
        (("codebase-memory",), "[[codebase-memory-workflow]]"),
        (("export", "public", "client-facing"), "[[vault-operating-model#Public vs Private Boundary]]"),
        (("schedule", "automation", "deterministic"), "[[deterministic-automation]]"),
        (("heartbeat", "autonomous"), "[[autonomous-agent-heartbeats]]"),
        (("slack",), "[[slack-agent-command-center]]"),
        (("chatgpt",), "[[chatgpt-archive-selective-review-workflow]]"),
    ):
        if any(marker in text for marker in markers):
            links.append(link)
    if any(meta.get(key) for key in ("worker_role", "model_tier", "capability_requirements")):
        links.append("[[worker-capability-routing]]")
    if meta.get("verification_commands") or "tests" in str(meta.get("capability_requirements", "")).lower():
        links.append("[[test-discovery-convention]]")
    return links


def recent_tasks(work_root: Path, top: int, column: str = "ready") -> str:
    status_label = RECENT_COLUMNS[column]
    entries = []
    folder = work_root / column
    if folder.exists():
        for path in folder.glob("*.md"):
            meta, _ = split_task(path)
            if meta.get("status") != status_label:
                continue
            entries.append((task_created_date(meta, path), path.stem, meta.get("title", path.stem)))
    entries.sort(reverse=True)
    lines = [f"# Recent {status_label} Tasks"]
    if not entries:
        return "\n".join(lines + ["  (none)"])
    for created, stem, title in entries[:top]:
        lines.append(f"[{status_label}] {created.isoformat()} {stem} — {title}")
    return "\n".join(lines)


def reconciliation_deltas(results: list) -> list[str]:
    deltas = []
    for result in results:
        if result.unblocked:
            deltas.append(f"unblocked {result.path.name}")
        elif result.pruned:
            deltas.append(f"pruned {result.path.name}: {', '.join(result.pruned_deps)}")
    return deltas


def render_shortlist(candidates: list[Candidate], top: int) -> str:
    lines = ["# Eligible READY Tasks"]
    if not candidates:
        return "\n".join(lines + ["  (none)"])
    for index, candidate in enumerate(candidates[:top], 1):
        lines.append(f"{index}. {candidate.task_id} - {candidate.meta.get('title', candidate.task_id)}")
        lines.append(f"   {', '.join(candidate.reasons)}")
    return "\n".join(lines)


def render_claim_receipt(candidate: Candidate, work_root: Path, deltas: list[str], lease_until: str) -> str:
    """Minimal routing receipt after a successful claim.

    Workers read the claimed Markdown task for static content (DoD, Activity,
    relationships). This receipt carries only computed routing signals.
    """
    meta = candidate.meta
    try:
        display_path = candidate.path.relative_to(VAULT_ROOT)
    except ValueError:
        display_path = candidate.path
    lines = [
        f"path: {display_path}",
        f"lease: {lease_until}",
        f"approval: leo_review_required={bool(meta.get('leo_review_required'))}",
    ]
    for key in ("worker_role", "capability_requirements", "model_tier", "required_tools", "verification_commands"):
        if meta.get(key):
            lines.append(f"{key}: {meta[key]}")
    lines.append("\n## Dependency Deltas")
    lines.extend([f"- {delta}" for delta in deltas] or ["  (none)"])
    lines.append("\n## Required Policy Links")
    links = required_policy_links(meta)
    lines.extend(f"- {link}" for link in links)
    if not links:
        lines.append("  (none)")
    return "\n".join(lines)


def render_packet(candidate: Candidate, work_root: Path, deltas: list[str]) -> str:
    """Full task packet for --full-packet mode or remote dispatchers without filesystem access."""
    meta = candidate.meta
    try:
        display_path = candidate.path.relative_to(VAULT_ROOT)
    except ValueError:
        display_path = candidate.path
    lines = [
        "", "# Selected Task Packet", f"id: {candidate.task_id}",
        f"title: {meta.get('title', '')}", f"path: {display_path}",
        f"approval: leo_review_required={bool(meta.get('leo_review_required'))}",
    ]
    for key in ("worker_role", "capability_requirements", "model_tier", "required_tools", "verification_commands"):
        if meta.get(key):
            lines.append(f"{key}: {meta[key]}")
    lines.append("\n## Definition Of Done")
    lines.extend(definition_of_done(candidate.body) or ["  (none)"])
    lines.append("\n## Recent Activity")
    lines.extend(recent_activity(candidate.body) or ["  (none)"])
    lines.append("\n## Dependency Deltas")
    lines.extend([f"- {delta}" for delta in deltas] or ["  (none)"])
    lines.append("\n## Required Policy Links")
    lines.extend(f"- {link}" for link in required_policy_links(meta))
    record = TaskRecord(candidate.task_id, str(meta.get("status", "")), candidate.path, meta, candidate.body)
    lines.append("\n" + render_report(record, build_index(work_root), compact=True).rstrip())
    return "\n".join(lines)


def select_explicit(task: str, work_root: Path) -> Candidate:
    path = resolve_task_path(Path(task), work_root)
    meta, body = split_task(path)
    if path.parent != work_root / "ready" or meta.get("status") != "READY":
        raise ValueError("explicit selection requires a READY task in work/ready")
    if parse_blocked_by(meta.get("blocked_by")):
        raise ValueError("explicit selection still has hard blockers")
    return rank_task(path, meta, body)


def claim(candidate: Candidate, args: argparse.Namespace) -> Path:
    return apply_action(argparse.Namespace(
        action="claim", task=candidate.path, agent=args.agent,
        session_id=args.session_id, minutes=args.minutes, work_root=args.work_root, now=None,
    ))


def run(args: argparse.Namespace) -> int:
    work_root = args.work_root.resolve()
    if args.action == "list" and args.recent:
        print(recent_tasks(
            work_root,
            args.top if args.top != 5 else 10,
            getattr(args, "recent_column", None) or "ready",
        ))
        return 0
    deltas = reconciliation_deltas(reconcile_all(work_root, agent=args.agent))
    candidates = eligible_candidates(work_root, include_review=args.include_review)
    if args.action == "list":
        print(render_shortlist(candidates, args.top))
        return 0
    if not args.session_id:
        raise ValueError("claim requires --session-id")
    auto_candidates = eligible_candidates(work_root)
    selected = select_explicit(args.task, work_root) if args.task else (auto_candidates[0] if auto_candidates else None)
    if selected is None:
        raise ValueError("no eligible READY tasks")
    destination = claim(selected, args)
    claimed_meta, claimed_body = split_task(destination)
    claimed_candidate = rank_task(destination, claimed_meta, claimed_body)
    lease_until = str(claimed_meta.get("lease_until", "unknown"))
    try:
        display_dest = destination.relative_to(VAULT_ROOT)
    except ValueError:
        display_dest = destination
    print(f"\nCLAIMED {display_dest}")
    if getattr(args, "full_packet", False):
        print(render_packet(claimed_candidate, work_root, deltas))
    else:
        print(render_claim_receipt(claimed_candidate, work_root, deltas, lease_until))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "claim"))
    parser.add_argument("--task", help="Explicit READY task path or bare task ID.")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session-id")
    parser.add_argument("--minutes", type=int, default=120)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--include-review", action="store_true", help="Include Leo-review tasks in listing.")
    parser.add_argument("--recent", action="store_true", help="Show recently created READY tasks. Only valid with list.")
    parser.add_argument(
        "--recent-column",
        choices=tuple(RECENT_COLUMNS),
        default=None,
        help="Lifecycle column for --recent output. Defaults to ready.",
    )
    parser.add_argument("--full-packet", action="store_true", help="Print full task packet on claim (DoD, Activity, relationships). For remote dispatchers without filesystem access.")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.minutes < 1:
        parser.error("--minutes must be at least 1")
    if getattr(args, "recent", False) and args.action == "claim":
        parser.error("--recent is not valid with claim")
    if args.recent_column and not args.recent:
        parser.error("--recent-column requires --recent")
    return args


def main() -> None:
    try:
        raise SystemExit(run(parse_args()))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
