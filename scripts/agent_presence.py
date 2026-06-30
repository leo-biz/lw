#!/usr/bin/env python3
"""Track local agent-session presence with expiring state and JSONL events.

Policy — read before modifying this file:
  wiki/07-systems/agent-presence-ledger.md     lifecycle states, logging rules, expiry
  wiki/07-systems/multi-agent-coordination.md  session fields and coordination model
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = VAULT_ROOT / "runs"
DEFAULT_STATE = RUNS_DIR / "agent-presence.json"
DEFAULT_EVENTS = RUNS_DIR / "agent-presence.jsonl"
DEFAULT_LOCK = RUNS_DIR / ".agent-presence.lock"
ACTIVE_STATUSES = {"STARTED", "ACTIVE", "CHECKPOINTED", "WAITING_APPROVAL", "BLOCKED"}
TERMINAL_STATUSES = {"COMPLETED", "STOPPED"}
ALL_STATUSES = ACTIVE_STATUSES | TERMINAL_STATUSES


def now_local() -> datetime:
    return datetime.now().astimezone()


def iso_time(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@contextmanager
def state_lock(lock_path: Path):
    try:
        lock_path.mkdir(parents=True)
    except FileExistsError as exc:
        raise RuntimeError(f"presence update already in progress: {lock_path}") from exc
    try:
        yield
    finally:
        shutil.rmtree(lock_path)


def load_state(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_state(path: Path, state: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as tmp:
        json.dump(state, tmp, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def append_event(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def visible_status(entry: dict, now: datetime) -> str:
    status = entry["status"]
    if status in ACTIVE_STATUSES and parse_time(entry["lease_until"]) <= now:
        return "EXPIRED"
    return status


def format_duration(started_at: str, ended_at: str) -> str:
    seconds = max(0, int((parse_time(ended_at) - parse_time(started_at)).total_seconds()))
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    hours, remaining_minutes = divmod(minutes, 60)
    return f"{hours} hr {remaining_minutes} min"


def print_closing_summary(entry: dict) -> None:
    tasks = entry.get("tasks", [])
    print(f"Session ended: {entry['agent']}@{entry['provider']}:{entry['session_id']}")
    print(f"  started: {entry['started_at']}")
    print(f"  ended:   {entry['last_seen']}  ({format_duration(entry['started_at'], entry['last_seen'])})")
    print(f"  tasks:   {', '.join(tasks) if tasks else '(none)'}")
    print(f"  commit:  {entry['last_commit'] or '(none)'}")
    print(f"  next:    {entry['handoff_checkpoint'] or '(none)'}")


def update_presence(args: argparse.Namespace) -> None:
    now = args.now or now_local()
    lease_until = now + timedelta(minutes=args.minutes)
    event_action = args.action
    if args.action == "complete":
        print("WARNING: complete is deprecated; use end.", file=sys.stderr)
        event_action = "end"
    with state_lock(args.lock):
        state = load_state(args.state)
        previous = state.get(args.session_id, {})
        if args.action != "start" and not previous:
            raise ValueError("session is not registered; run start first")
        restarted = args.action == "start" and previous.get("status") in TERMINAL_STATUSES
        if restarted:
            previous = {}
            event_action = "restart"
        tasks = list(previous.get("tasks", []))
        previous_task_id = previous.get("task_id", "")
        if previous_task_id and previous_task_id not in tasks:
            tasks.append(previous_task_id)
        if args.task_id and args.task_id not in tasks:
            tasks.append(args.task_id)
        entry = {
            "agent": args.agent or previous.get("agent", ""),
            "provider": args.provider or previous.get("provider", ""),
            "session_id": args.session_id,
            "session_url": args.session_url or previous.get("session_url", ""),
            "task_id": args.task_id or previous.get("task_id", ""),
            "tasks": tasks,
            "role": args.role or previous.get("role", ""),
            "model": args.model or previous.get("model", ""),
            "strengths": args.strengths or previous.get("strengths", []),
            "tools": args.tools or previous.get("tools", []),
            "cost_tier": args.cost_tier or previous.get("cost_tier", ""),
            "context_tier": args.context_tier or previous.get("context_tier", ""),
            "status": args.status,
            "started_at": previous.get("started_at", iso_time(now)),
            "last_seen": iso_time(now),
            "lease_until": iso_time(lease_until),
            "current_slice": args.current_slice or previous.get("current_slice", ""),
            "last_commit": args.last_commit or previous.get("last_commit", ""),
            "handoff_checkpoint": args.handoff_checkpoint or previous.get("handoff_checkpoint", ""),
        }
        state[args.session_id] = entry
        write_state(args.state, state)
        append_event(args.events, {"time": iso_time(now), "event": event_action, **entry})
    if event_action == "end" or args.action == "stop":
        print_closing_summary(entry)
    else:
        print(f"{entry['status']} {entry['agent']}@{entry['provider']}:{entry['session_id']} | {entry['current_slice']}")


def show_status(args: argparse.Namespace) -> None:
    now = args.now or now_local()
    entries = list(load_state(args.state).values())
    entries.sort(key=lambda item: item.get("last_seen", ""), reverse=True)
    if not entries:
        print("No agent sessions recorded.")
        return

    use_json = getattr(args, "json", False)

    if use_json:
        result = []
        for entry in entries:
            row = dict(entry)
            row["visible_status"] = visible_status(entry, now)
            result.append(row)
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    active_count = sum(1 for e in entries if visible_status(e, now) in ACTIVE_STATUSES)
    completed_count = sum(1 for e in entries if visible_status(e, now) in TERMINAL_STATUSES)
    expired_count = sum(1 for e in entries if visible_status(e, now) == "EXPIRED")
    print(f"{len(entries)} session(s): {active_count} active, {completed_count} completed, {expired_count} expired")

    for entry in entries:
        status = visible_status(entry, now)
        agent_str = f"{entry['agent']}@{entry['provider']}:{entry['session_id']}"
        print(f"\n{status:<18} {agent_str}")
        if entry.get("task_id"):
            print(f"  task:   {entry['task_id']}")
        model_parts = []
        if entry.get("model"):
            model_parts.append(entry["model"])
        if entry.get("role"):
            model_parts.append(f"({entry['role']})")
        if model_parts:
            print(f"  model:  {' '.join(model_parts)}")
        if entry.get("started_at"):
            print(f"  started:{entry['started_at']}")
        seen_line = f"seen:   {entry['last_seen']}"
        if entry.get("last_commit"):
            seen_line += f"  commit: {entry['last_commit']}"
        print(f"  {seen_line}")
        if entry.get("current_slice"):
            print(f"  slice:  {entry['current_slice']}")
        if entry.get("handoff_checkpoint"):
            print(f"  next:   {entry['handoff_checkpoint']}")


def prune_state(args: argparse.Namespace) -> None:
    now = args.now or now_local()
    with state_lock(args.lock):
        state = load_state(args.state)
        kept = {}
        removed = []
        for session_id, entry in state.items():
            status = visible_status(entry, now)
            last_seen = parse_time(entry["last_seen"])
            if status in TERMINAL_STATUSES and last_seen + timedelta(hours=args.terminal_hours) <= now:
                removed.append(session_id)
            elif status == "EXPIRED" and last_seen + timedelta(hours=args.expired_hours) <= now:
                removed.append(session_id)
            else:
                kept[session_id] = entry
        write_state(args.state, kept)
    print(f"PRUNED {len(removed)} session(s).")


def common_update(parser: argparse.ArgumentParser, status: str) -> None:
    parser.add_argument("--agent", default="")
    parser.add_argument("--provider", default="")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--session-url", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--strengths", nargs="*", default=[])
    parser.add_argument("--tools", nargs="*", default=[])
    parser.add_argument("--cost-tier", default="")
    parser.add_argument("--context-tier", default="")
    parser.add_argument("--current-slice", default="")
    parser.add_argument("--last-commit", default="")
    parser.add_argument("--handoff-checkpoint", default="")
    parser.add_argument("--minutes", type=int, default=45)
    parser.set_defaults(run=update_presence, status=status)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE, help=argparse.SUPPRESS)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS, help=argparse.SUPPRESS)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK, help=argparse.SUPPRESS)
    parser.add_argument("--now", type=parse_time, help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="action", required=True)

    common_update(subparsers.add_parser("start"), "STARTED")
    common_update(subparsers.add_parser("heartbeat"), "ACTIVE")
    common_update(subparsers.add_parser("checkpoint"), "CHECKPOINTED")
    common_update(subparsers.add_parser("wait"), "WAITING_APPROVAL")
    common_update(subparsers.add_parser("block"), "BLOCKED")
    common_update(subparsers.add_parser("end"), "COMPLETED")
    common_update(subparsers.add_parser("complete"), "COMPLETED")
    common_update(subparsers.add_parser("stop"), "STOPPED")

    status = subparsers.add_parser("status")
    status.add_argument("--json", action="store_true", help="Output JSON array")
    status.set_defaults(run=show_status)

    prune = subparsers.add_parser("prune")
    prune.add_argument("--terminal-hours", type=int, default=24)
    prune.add_argument("--expired-hours", type=int, default=72)
    prune.set_defaults(run=prune_state)

    args = parser.parse_args()
    args.state = args.state.resolve()
    args.events = args.events.resolve()
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
