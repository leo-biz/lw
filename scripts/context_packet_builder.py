#!/usr/bin/env python3
"""Build compact context packets for fresh agent sessions and Slack previews.

Policy:
  wiki/07-systems/queue-worker-bootstrap.md      compact packet fields
  wiki/07-systems/multi-agent-coordination.md    approval and relationship boundaries
  wiki/07-systems/agent-control-plane-operating-model.md  session semantics

Usage:
  python3 scripts/context_packet_builder.py task-2026-06-04-example
  python3 scripts/context_packet_builder.py work/ready/example.md --type review
  python3 scripts/context_packet_builder.py task-2026-06-04-example --audience public

Tests:
  python3 -m unittest scripts.tests.test_context_packet_builder -v
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from scripts.pick_next_task import (
        definition_of_done,
        recent_activity,
        required_policy_links,
    )
    from scripts.task_relationship_report import (
        TaskRecord,
        build_index,
        render_report,
        resolve_task_path,
        split_task,
    )
except ModuleNotFoundError:  # Direct execution from scripts/.
    from pick_next_task import definition_of_done, recent_activity, required_policy_links
    from task_relationship_report import (
        TaskRecord,
        build_index,
        render_report,
        resolve_task_path,
        split_task,
    )

VAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORK_ROOT = VAULT_ROOT / "work"
PACKET_TYPES = ("task-worker", "read-only-chat", "review", "ask-many")
PRIVATE_AUDIENCE = "private/internal"
EXTERNAL_AUDIENCES = ("public", "client-facing")
AUDIENCES = (PRIVATE_AUDIENCE, *EXTERNAL_AUDIENCES)


@dataclass(frozen=True)
class ContextPacket:
    task_id: str
    packet_type: str
    audience: str
    text: str
    blocked: bool = False


def _as_list(value: object) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(VAULT_ROOT))
    except ValueError:
        return str(path)


def _task_audience(meta: dict) -> str:
    return str(meta.get("audience") or PRIVATE_AUDIENCE)


def audience_allowed(meta: dict, requested: str) -> bool:
    """Return whether this task may be packetized for requested audience."""
    if requested not in AUDIENCES:
        raise ValueError(f"audience must be one of: {', '.join(AUDIENCES)}")
    if requested == PRIVATE_AUDIENCE:
        return True
    task_audience = _task_audience(meta)
    return task_audience == requested


def _safe_title(meta: dict, path: Path) -> str:
    return str(meta.get("title") or path.stem)


def _metadata_lines(meta: dict, path: Path) -> list[str]:
    fields = (
        "status", "priority", "quadrant", "domain", "workstream",
        "execution_mode", "human_effort", "ai_effort", "human_input",
    )
    lines = [
        f"id: {meta.get('id', path.stem)}",
        f"title: {_safe_title(meta, path)}",
        f"path: {_display_path(path)}",
    ]
    for key in fields:
        if meta.get(key) not in (None, "", []):
            lines.append(f"{key}: {meta[key]}")
    return lines


def _session_lines(meta: dict) -> list[str]:
    fields = ("agent", "claimed_at", "lease_until", "session_id", "session_provider", "session_url", "last_activity")
    lines = [f"{key}: {meta.get(key)}" for key in fields if meta.get(key)]
    return lines or ["  (none)"]


def _link_lines(meta: dict) -> list[str]:
    fields = ("source", "wiki_page", "repo", "export")
    lines: list[str] = []
    for key in fields:
        for value in _as_list(meta.get(key)):
            lines.append(f"- {key}: {value}")
    return lines or ["  (none)"]


def _approval_lines(meta: dict, packet_type: str, audience: str) -> list[str]:
    lines = [
        f"packet_type: {packet_type}",
        f"audience: {audience}",
        f"leo_review_required: {bool(meta.get('leo_review_required'))}",
    ]
    if meta.get("human_input"):
        lines.append(f"human_input: {meta['human_input']}")
    if packet_type == "read-only-chat":
        lines.append("mode_ceiling: read/suggest only; no vault writes, worker launches, or durable memory saves")
    elif packet_type == "review":
        lines.append("mode_ceiling: report-only review unless separately authorized")
    elif packet_type == "ask-many":
        lines.append("mode_ceiling: report-only multi-agent comparison; participants must not edit shared files")
    else:
        lines.append("mode_ceiling: task worker must follow task lease, file claims, and approval gates")
    return lines


def _verification_lines(meta: dict) -> list[str]:
    values = _as_list(meta.get("verification_commands"))
    return [f"- {value}" for value in values] if values else ["  (none listed)"]


def _relationship_text(task_id: str, meta: dict, body: str, path: Path, work_root: Path) -> str:
    record = TaskRecord(task_id, str(meta.get("status", "")), path, meta, body)
    return render_report(record, build_index(work_root), compact=True).rstrip()


def blocked_packet(task_id: str, meta: dict, path: Path, packet_type: str, audience: str) -> ContextPacket:
    lines = [
        "# Context Packet Blocked",
        "",
        "PACKET_BLOCKED_BY_AUDIENCE",
        "",
        f"id: {task_id}",
        f"path: {_display_path(path)}",
        f"requested_audience: {audience}",
        f"task_audience: {_task_audience(meta)}",
        "",
        "This task is not explicitly marked safe for the requested public/client-facing audience.",
        "Generate a private/internal packet or create a reviewed public-safe export first.",
    ]
    return ContextPacket(task_id, packet_type, audience, "\n".join(lines), blocked=True)


def build_packet(
    task: str | Path,
    *,
    packet_type: str = "task-worker",
    audience: str = PRIVATE_AUDIENCE,
    prompt: str = "",
    work_root: Path = DEFAULT_WORK_ROOT,
    activity_limit: int = 5,
) -> ContextPacket:
    if packet_type not in PACKET_TYPES:
        raise ValueError(f"packet_type must be one of: {', '.join(PACKET_TYPES)}")
    work_root = work_root.resolve()
    path = resolve_task_path(Path(task), work_root)
    meta, body = split_task(path)
    task_id = str(meta.get("id") or path.stem)

    if not audience_allowed(meta, audience):
        return blocked_packet(task_id, meta, path, packet_type, audience)

    lines = [
        "# Context Packet",
        "",
        "## Packet",
        *_approval_lines(meta, packet_type, audience),
        "",
        "## Task",
        *_metadata_lines(meta, path),
        "",
        "## Session Status",
        *_session_lines(meta),
        "",
        "## Definition Of Done",
        *(definition_of_done(body) or ["  (none)"]),
        "",
        "## Recent Activity",
        *(recent_activity(body, limit=activity_limit) or ["  (none)"]),
        "",
        "## Relevant Links",
        *_link_lines(meta),
        "",
        "## Required Policy Links",
        *([f"- {link}" for link in required_policy_links(meta)] or ["  (none)"]),
        "",
        "## Verification Commands",
        *_verification_lines(meta),
        "",
        "## Relationships",
        _relationship_text(task_id, meta, body, path, work_root),
    ]
    if prompt:
        lines.extend(["", "## Requested Prompt", prompt])
    return ContextPacket(task_id, packet_type, audience, "\n".join(lines).rstrip() + "\n")


def packet_to_json(packet: ContextPacket) -> str:
    return json.dumps({
        "task_id": packet.task_id,
        "packet_type": packet.packet_type,
        "audience": packet.audience,
        "blocked": packet.blocked,
        "text": packet.text,
    }, indent=2)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Task path or bare task ID.")
    parser.add_argument("--type", choices=PACKET_TYPES, default="task-worker", dest="packet_type")
    parser.add_argument("--audience", choices=AUDIENCES, default=PRIVATE_AUDIENCE)
    parser.add_argument("--prompt", default="", help="Optional user prompt to append to the packet.")
    parser.add_argument("--json", action="store_true", help="Emit JSON wrapper instead of plain Markdown.")
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK_ROOT, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    packet = build_packet(
        args.task,
        packet_type=args.packet_type,
        audience=args.audience,
        prompt=args.prompt,
        work_root=args.work_root,
    )
    print(packet_to_json(packet) if args.json else packet.text, end="" if packet.text.endswith("\n") else "\n")
    return 2 if packet.blocked else 0


def main() -> None:
    try:
        raise SystemExit(run(parse_args()))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
