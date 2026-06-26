---
title: Continuation Operator Card
node_type: reference
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - codex
  - claude-code
  - goals
  - loops
  - continuation
  - operator-card
  - ai-reviewed
created: 2026-06-08
updated: 2026-06-08
---

# Continuation Operator Card

Provider-native continuation controls are execution helpers. They operate inside
the vault's durable task contract. The vault remains the source of truth for
work selection, leases, file ownership, checkpoints, completion proof, and
approval boundaries.

See [[codex-claude-goal-loop-continuation-direction]] for the full direction
and open questions.

## Control Summary

| Control | Provider | Trigger | Normal stop |
|---|---|---|---|
| `/goal <condition>` | Claude Code | previous turn finishes | evaluator confirms condition |
| `/loop [interval] [prompt]` | Claude Code | time interval elapses | user stops, loop self-exits, or seven-day expiry |
| `/goal <objective>` | Codex CLI / Codex app | explicit request | `/goal clear` or objective satisfied |
| Thread automation | Codex app | scheduled wake-up | automation disabled or deleted |

### Claude `/goal`

- One session-scoped completion condition at a time; starts work immediately.
- Evaluator checks the condition after each turn with a fast model.
- Surfaces elapsed time, evaluated turns, and token spend via `/goal`.
- Survives `--resume` or `--continue`; turn count, timer, and token baseline
  reset on resume.
- Accepts a condition up to 4,000 characters.
- Clears automatically when achieved; supports `/goal clear`.

### Claude `/loop`

- Schedules a repeated prompt while the session stays open.
- Accepts an interval, dynamic cadence, or bare maintenance mode.
- `Esc` cancels a pending wake-up.
- Restores unexpired scheduled tasks after resume; seven-day expiry.
- Inherits session permissions; does not bypass approval boundaries.
- **Bare maintenance loop is broader than the vault queue-worker contract.**
  Always use an explicit narrow prompt or a reviewed `.claude/loop.md` for
  vault work — not the bare maintenance default.

### Codex `/goal`

- Durable thread objective; set with `/goal <objective>`, inspect with `/goal`.
- Controls: `/goal pause`, `/goal resume`, `/goal clear`.
- Attached to the active thread while work continues.
- Use a clear validation loop and verifiable stopping condition.

### Codex Thread Automations

- Recurring heartbeat-style wake-ups attached to one thread.
- Use when a scheduled run must preserve conversation context.
- Use standalone or project automations when each run should start fresh.

## Completion Contract Fields

Fill these fields before using any continuation control for vault work:

```text
observable outcome:   [single measurable result, not an open backlog]
bounded slice:        [scope that fits this run with margin]
proof required:       [command, artifact, or diff that confirms the outcome]
stop when:            [explicit condition or resource signal that ends the run]
checkpoint when:      [before each substantial phase, before interruption]
approval boundary:    [what requires Leo sign-off before proceeding]
next-task rule:       [dependent/related only; budget preflight must pass first]
```

### Next-Task Flow

```text
finish and prove the current bounded slice
-> checkpoint-commit with attribution
-> close or renew the task lease
-> run continuation preflight (see [[provider-budget-preflight-operator-card]])
-> claim at most one eligible dependent, related, or same-workstream task
   only when work, validation, and handoff reserve fit with margin
-> otherwise stop with a durable next action
```

## Critical Rules

**Provider evaluator success does not replace the
[[agent-completion-proof-protocol]].** When a `/goal` evaluator reports the
condition satisfied, that is a signal — not proof. Run the vault completion
proof protocol, record evidence, and write a durable checkpoint before closing
the lease.

**Schedules, broader autonomy, and project-level `.claude/loop.md` changes
require Leo approval.** Do not create scheduled wake-ups, enable recurring
automations, broaden the autonomy boundary, or install a project-level
`.claude/loop.md` without an explicit Leo approval step.

## Operating Rules

1. Use one task or one coherent slice per goal. Never pass an open backlog.
2. State a measurable stopping condition and the command or artifact that proves it.
3. Include a shutdown reserve and a fallback stop rule when exact usage is
   unavailable.
4. Checkpoint before a substantial new phase, before provider interruption, and
   before claiming related work.
5. Keep normal task-lease, presence, file-claim, and approval rules active
   throughout.
6. Treat provider evaluator completion as a signal, then run vault completion
   proof before closing the lease.
7. Use explicit prompts for Claude `/loop`; do not rely on the bare maintenance
   prompt for queue work.
8. Do not create schedules, broaden autonomy, or install provider automation
   without Leo approval.

## Provider vs Vault Responsibility

| Provider behavior | Vault responsibility |
|---|---|
| objective or completion condition | task Definition of Done and bounded slice |
| thread/session continuity | task lease, `session_id`, presence ledger, checkpoint |
| token, turn, or duration display | continuation preflight input when available |
| repeated scheduled wake-up | heartbeat runner or reviewed provider automation |
| provider evaluator says done | [[agent-completion-proof-protocol]] + recorded evidence |
| provider resume | compact task packet and durable handoff checkpoint |

## Linked Nodes

- direction: [[codex-claude-goal-loop-continuation-direction]]
- implements: [[autonomous-agent-heartbeats]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[provider-budget-preflight-operator-card]]
- related_to: [[agent-completion-proof-protocol]]
- related_to: [[multi-agent-coordination]]
