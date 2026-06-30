#!/usr/bin/env python3
"""Best-effort presence updates for deterministic workflow helpers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
PRESENCE_SCRIPT = VAULT_ROOT / "scripts" / "agent_presence.py"
PRESENCE_STATE = VAULT_ROOT / "runs" / "agent-presence.json"


def update_presence_best_effort(
    action: str,
    *,
    session_id: str,
    agent: str = "",
    task_id: str = "",
    last_commit: str = "",
    current_slice: str = "",
) -> None:
    """Update an existing presence record without blocking the primary helper."""
    try:
        if not PRESENCE_STATE.exists():
            return
        state = json.loads(PRESENCE_STATE.read_text())
        if session_id not in state:
            return
        command = [
            sys.executable,
            str(PRESENCE_SCRIPT),
            action,
            "--session-id",
            session_id,
        ]
        for option, value in (
            ("--agent", agent),
            ("--task-id", task_id),
            ("--last-commit", last_commit),
            ("--current-slice", current_slice),
        ):
            if value:
                command.extend((option, value))
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode:
            message = result.stderr.strip() or result.stdout.strip() or "presence update failed"
            print(f"WARNING: presence update failed: {message}", file=sys.stderr)
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        print(f"WARNING: presence update failed: {exc}", file=sys.stderr)
