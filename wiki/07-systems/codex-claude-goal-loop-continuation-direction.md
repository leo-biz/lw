---
title: Codex And Claude Goal Loop Continuation Direction
node_type: direction
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
  - ai-reviewed
created: 2026-06-01
updated: 2026-06-01
---

# Codex And Claude Goal Loop Continuation Direction

## Decision

Use provider-native continuation controls only as execution helpers inside the
vault's durable task contract. The vault remains the source of truth for work
selection, leases, file ownership, checkpoints, proof, and approval boundaries.

Do not treat a provider thread, `/goal`, `/loop`, or an app automation as an
open-ended backlog worker. Give each run one observable outcome, one bounded
slice, proof requirements, and explicit stop conditions.

## Research Snapshot

Verified on 2026-06-01:

- Installed local versions: `codex-cli 0.135.0-alpha.1` and Claude Code
  `2.1.159`.
- Codex CLI reports `goals` as `stable` and enabled. It reports
  `runtime_metrics` as `under development` and disabled.
- The Codex thread runtime exposed a goal-status read with no active goal and no
  remaining-token or completion-budget report. No goal was created during this
  research because creating one requires an explicit request.
- Claude Code `2.1.159` is above the documented minimum versions for `/loop`
  (`2.1.72`) and Claude `/goal` (`2.1.139`).

## Verified Provider Behavior

### Claude Code

Official Claude Code documentation distinguishes two controls:

| Control | Trigger for the next turn | Normal stop |
|---|---|---|
| `/goal <condition>` | previous turn finishes | evaluator confirms the completion condition |
| `/loop [interval] [prompt]` | time interval elapses | user stops it, self-paced loop decides work is done, or seven-day expiry |

Claude `/goal`:

- keeps one session-scoped completion condition active at a time
- starts work immediately when set
- checks the condition after each turn with a small fast evaluator model
- surfaces duration, evaluated turns, current token spend, and the evaluator's
  latest reason through `/goal`
- accepts a condition up to 4,000 characters
- can restore an unfinished goal after `--resume` or `--continue`, while its
  turn count, timer, and token-spend baseline reset
- clears automatically when achieved and supports `/goal clear`

Claude `/loop`:

- schedules a repeated prompt while the session stays open
- accepts an interval and prompt, a prompt with dynamic cadence, or a bare
  maintenance loop
- lets `Esc` stop a pending `/loop` wake-up
- restores unexpired session-scoped scheduled tasks after resume
- expires recurring tasks after seven days
- inherits session permissions and does not bypass approval boundaries

The bare Claude maintenance loop may continue unfinished conversation work,
tend the current branch pull request, and run cleanup passes. That default is
broader than the vault queue-worker contract, so vault work should use an
explicit narrow prompt or a reviewed `.claude/loop.md`.

### Codex

Official Codex documentation describes `/goal` as a durable thread objective
for long-running work:

- set with `/goal <objective>`
- inspect with `/goal`
- control with `/goal pause`, `/goal resume`, and `/goal clear`
- keep the goal attached to the active thread while work continues
- use a clear validation loop and verifiable stopping condition

Codex CLI `/status` displays session configuration and token usage, including
remaining context capacity. Codex app thread automations are recurring
heartbeat-style wake-ups attached to one thread. Use them when a scheduled run
must preserve conversation context; use standalone or project automations when
each run should start fresh.

Official Codex docs describe eval-driven improvement loops as a workflow
pattern, not as a documented `/loop` slash command.

## Sources

- Claude Code scheduled tasks:
  https://code.claude.com/docs/en/scheduled-tasks
- Claude Code goals:
  https://code.claude.com/docs/en/goal
- Codex CLI slash commands:
  https://developers.openai.com/codex/cli/slash-commands
- Codex goal use case:
  https://developers.openai.com/codex/use-cases/follow-goals
- Codex app features and thread automations:
  https://developers.openai.com/codex/app/features
- Codex app automations:
  https://developers.openai.com/codex/app/automations
- Codex eval-driven iteration use case:
  https://developers.openai.com/codex/use-cases/iterate-on-difficult-problems

## Observations And Inferences

Verified observation:

- Claude exposes documented elapsed time, evaluated-turn count, and token spend
  for an active `/goal`.
- Codex CLI documents `/status` token usage and remaining context capacity.
- This Codex Desktop thread's goal-status API can surface goal state,
  elapsed-time and token-budget data when available, but this thread currently
  returned no active goal and no budget report.

Inference:

- Provider-native signals can improve preflight when present, but the runner
  must not require them. They are not a portable cross-provider contract and
  may reset on resume.

Open questions:

- Confirm Codex Desktop goal pause, resume, clear, budget, and blocked-state UX
  in a disposable explicitly requested goal run.
- Confirm whether Codex Desktop thread automations expose a stable
  machine-readable run budget suitable for the local heartbeat runner.
- Decide whether a project-level `.claude/loop.md` is useful after the operator
  card has been reviewed. Do not add one implicitly.

## Vault Comparison

| Provider behavior | Vault responsibility |
|---|---|
| objective or completion condition | task Definition of Done and bounded slice |
| thread/session continuity | task lease, `session_id`, presence ledger, checkpoint |
| token, turn, or duration display | continuation preflight input when available |
| repeated scheduled wake-up | heartbeat runner or reviewed provider automation |
| provider evaluator says done | completion-proof protocol and recorded evidence |
| provider resume | compact task packet and durable handoff checkpoint |

Provider controls improve execution continuity. They do not replace
[[task-system]], [[file-claim-ledger]], [[agent-presence-ledger]],
[[agent-completion-proof-protocol]], or [[autonomous-agent-heartbeats]].

## Minimum Guardrails

1. Use one task or one coherent slice per goal. Never pass an open backlog as a
   goal.
2. State a measurable stopping condition and the command or artifact that
   proves it.
3. Include a shutdown reserve and a fallback stop rule when exact usage is
   unavailable.
4. Checkpoint before a substantial new phase, before provider interruption, and
   before claiming related work.
5. Keep normal task-lease, presence, file-claim, and approval rules active.
6. Treat provider evaluator completion as a signal, then run vault completion
   proof before closing the lease.
7. Use explicit prompts for Claude `/loop`; do not rely on its broader bare
   maintenance prompt for queue work.
8. Do not create schedules, broaden autonomy, or install provider automation
   without Leo approval.

## Completion Contract

Every provider-assisted continuation run should state:

```text
observable outcome:
bounded slice:
proof required:
stop when:
checkpoint when:
approval boundary:
next-task rule:
```

Default next-task rule:

```text
finish and prove the current bounded slice
-> checkpoint-commit with attribution
-> close or renew the task lease
-> run continuation preflight
-> claim at most one eligible dependent, related, or same-workstream task
   only when work, validation, and handoff reserve fit with margin
-> otherwise stop with a durable next action
```

## Recommended First Slice

Add a short provider-continuation operator card and queue-worker prompt note
that map Claude `/goal`, Claude `/loop`, Codex `/goal`, and Codex thread
automations onto the completion contract above. Keep it documentation-only.
Do not enable schedules or create autonomous workers in that slice.

## Validation Steps

1. Review the operator card against the official provider pages linked above.
2. Run one disposable Claude `/goal` exercise with a bounded local proof.
3. Run one disposable Claude `/loop` exercise and stop it with `Esc`.
4. Run one explicitly requested disposable Codex `/goal` exercise and inspect
   goal status before clearing it.
5. Confirm each exercise leaves the vault task lease, presence state, and file
   claims coherent.

## Linked Nodes

- implements: [[autonomous-agent-heartbeats]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[agent-completion-proof-protocol]]
- related_to: [[multi-agent-coordination]]
