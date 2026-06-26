---
title: Agent Presence Ledger
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - coordination
  - activity
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Agent Presence Ledger

## Purpose

Make it obvious which agent sessions are active, waiting, blocked, finished, or
gone without reading provider chats or inferring state from dirty files.

Task leases answer who owns a task. File claims answer who expects to edit a
file. Presence answers: "who is here, what are they doing, and did they leave?"

## Local State

The deterministic helper writes Git-ignored local files:

```text
runs/agent-presence.json   current session state
runs/agent-presence.jsonl  append-only lifecycle events
```

Markdown task Activity and attributed Git commits remain the durable history.

## Provider Session IDs

Use the stable session ID the runtime exposes — do not generate a throwaway
timestamp. Generate `SID` once at the top of the session and reuse it across
all script calls.

| Provider | Env var | Notes |
|---|---|---|
| Claude Code | `$CLAUDE_CODE_SESSION_ID` | Stable UUID; resume via `claude --resume <ID>` |
| Codex Desktop | `$CODEX_THREAD_ID` | Thread identifier for the current conversation |
| Other | generate once | `SID="$(date +%s)-$AGENT"` as a last resort |

sqz injects `__SQZ_CMD=claude --resume` into the environment, giving the agent
its own resume command without hardcoding it:

```bash
SID="$CLAUDE_CODE_SESSION_ID"   # Claude Code
SID="$CODEX_THREAD_ID"          # Codex Desktop
echo "$__SQZ_CMD"               # prints: claude --resume
```

## Lifecycle

Use these states:

```text
STARTED
ACTIVE
CHECKPOINTED
WAITING_APPROVAL
BLOCKED
COMPLETED
STOPPED
EXPIRED
```

Example (Claude Code):

```bash
SID="$CLAUDE_CODE_SESSION_ID"

python3 scripts/agent_presence.py start \
  --agent claude \
  --provider anthropic \
  --session-id "$SID" \
  --task-id task-YYYY-MM-DD-example \
  --role coder \
  --model claude-sonnet-4-6 \
  --strengths "code analysis vault edits markdown python" \
  --tools "shell git sqz read edit" \
  --current-slice "Implement bounded helper"

python3 scripts/agent_presence.py heartbeat \
  --session-id "$SID" \
  --current-slice "Run focused tests"

python3 scripts/agent_presence.py end \
  --session-id "$SID" \
  --last-commit abc123 \
  --handoff-checkpoint "Assigned outcome complete."
```

Example (Codex Desktop):

```bash
SID="$CODEX_THREAD_ID"

python3 scripts/agent_presence.py start \
  --agent codex \
  --provider openai \
  --session-id "$SID" \
  --task-id task-YYYY-MM-DD-example \
  --role coder \
  --model gpt-5-codex \
  --strengths "code debugging tests" \
  --tools "shell git sqz" \
  --current-slice "Implement bounded helper"
```

## Inspect

```bash
python3 scripts/agent_presence.py status
```

Active entries expire when their lease elapses. An expired session is a signal
to inspect task Activity, file claims, and Git history before takeover.

Add truthful worker-profile fields when they are known. Follow
[[worker-capability-routing]]. Do not invent an exact model name, tier, or tool
that the runtime does not expose.

## Logging Rule

Log lifecycle milestones, not every keystroke:

```text
start
meaningful heartbeat during longer work
checkpoint commit
waiting for approval
blocked
completed
stopped before completion
```

Use Markdown task Activity for durable discoveries, decisions, blockers, and
completion proof. Keep noisy operational presence local.

Presence entries retain the latest `task_id` for compatibility and append each
distinct touched task to `tasks`. Use `end` when a session is finished.
`complete` remains a deprecated compatibility alias for older callers.

Starting a stable provider `session_id` again after its presence entry reached
`COMPLETED` or `STOPPED` begins a fresh lifecycle epoch. The current-state
record resets its start time, task list, and handoff fields so the closing
summary measures the new run accurately. The append-only JSONL log retains the
prior epoch and records the new event as `restart`.

Routine workflow helpers update existing presence records automatically:

```text
agent_commit.py checkpoint -> checkpoint
agent_commit.py complete   -> end
task_lease.py renew        -> heartbeat
task_lease.py release      -> stop
task_lease.py submit       -> wait
```

These updates are best-effort. A missing presence record is a silent no-op;
unexpected update failures warn without blocking the primary helper.

## Agent Rule

For substantial queue or vault work:

1. register presence when starting
2. claim the task and intended files
3. heartbeat during longer slices
4. checkpoint with the last commit and next action
5. mark `end`, `stop`, `wait`, or `block` before leaving
6. release file claims

## Verify

```bash
python3 -m unittest scripts.tests.test_agent_presence scripts.tests.test_agent_presence_bridge -v
python3 -m unittest scripts.tests.test_stale_agent_presence_monitor -v
```

Before committing shared helper behavior:

```bash
python3 -m unittest discover -s scripts/tests -v
```

## Linked Nodes

- implements: [[multi-agent-coordination]]
- related_to: [[file-claim-ledger]]
- related_to: [[agent-role-registry]]
- related_to: [[task-dashboard]]
- related_to: [[test-discovery-convention]]
- related_to: [[worker-capability-routing]]
