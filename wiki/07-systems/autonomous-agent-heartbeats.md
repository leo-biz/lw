---
title: Autonomous Agent Heartbeats
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - automation
  - heartbeats
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Autonomous Agent Heartbeats

## Purpose

Let AI workers initiate bounded useful work without waiting for Leo to manually prompt every session.

Autonomy should be explicit, budgeted, observable, and easy to stop. Routine deterministic work should remain normal scripts without AI tokens.

## Operating Model

```text
scheduler
-> wake worker role
-> read small role prompt and eligible queue only
-> stop immediately if no eligible work exists
-> claim one bounded task
-> load compact work packet
-> execute within autonomy and budget limits
-> validate
-> append activity and release, review, or complete task
-> preflight one related or newly-unblocked continuation
-> continue only when the next task fits with shutdown reserve
-> send meaningful summary or approval request
-> stop
```

The vault, not the provider thread, remembers the work.

## Two Wake-Up Types

### Deterministic Wake-Up

Use `launchd`, cron, or a local scheduler to run scripts directly:

```text
YouTube playlist polling
manifest refresh
dependency reconciliation
health-check scan
run-log summaries
```

No AI model should be called when the result can be computed predictably.

### AI Heartbeat

Wake an AI worker only when judgment adds value:

```text
review new transcript candidates
interpret a health-check report
research a READY task
draft a bounded internal output
execute an approved internal code task
```

## Task Eligibility

Only tasks explicitly marked as heartbeat-eligible may be selected automatically:

```yaml
heartbeat_eligible: true
autonomy: report_only
worker_role: reviewer
```

Allowed autonomy values:

| Value | Meaning |
|---|---|
| `manual` | Do not select automatically. Leo or a dispatcher assigns it. |
| `report_only` | Investigate and report. Do not apply substantive edits beyond logs, checkpoints, or a review artifact. |
| `execute_internal` | Perform reversible internal work, validate it, and stop at the task's normal review boundary. |
| `ask_first` | Prepare a compact action proposal and wait for Leo approval before execution. |

Default to:

```yaml
heartbeat_eligible: false
autonomy: manual
```

Do not infer eligibility from `execution_mode`. `execution_mode` describes who can perform the task. `autonomy` describes whether an unattended worker may act.

## Worker Budget

Each scheduled worker role should have a small configuration file with hard limits:

```yaml
role: transcript-reviewer
schedule: daily
max_tasks: 1
max_minutes: 20
max_cost_usd: 1.00
min_remaining_tokens: 8000
shutdown_reserve_minutes: 5
lease_minutes: 45
stop_if_no_work: true
default_autonomy: report_only
```

Start with conservative limits. A worker must stop before any budget is
exhausted and leave a compact checkpoint. Keep enough reserve to validate,
record activity, release or renew the lease, and write a handoff.

## Warm-Session Continuation

Starting a fresh worker has a context cost. After completing a task, an agent may
continue into another bounded task when the current context makes that work
materially cheaper and the next task fits safely inside the remaining budget.

Prefer the next task in this order:

1. an explicitly eligible dependent task newly unblocked by the completed work
2. an explicitly eligible task listed in `related_tasks`
3. an explicitly eligible task in the same workstream

The next task must still match the worker role, autonomy boundary, queue state,
and approval requirements. Relationships are retrieval and ranking hints, not
permission to bypass normal eligibility.

Before claiming any additional task, perform a continuation preflight:

```text
remaining time, token allowance, cost allowance, and context capacity
estimated context load, execution effort, validation effort, and handoff reserve
whether the next task can finish or reach a useful checkpoint before shutdown
```

Continue only when the estimate fits with margin. When exact provider token
usage is unavailable, use a conservative estimate and stop earlier. If the
estimate is uncertain, checkpoint and stop. Do not start a task merely to use
the rest of a context window.

`max_tasks` is a hard ceiling, not a target. Keep `max_tasks: 1` for early
pilots. Raise it only for a trusted role after reviewing real runs.

## Provider-Native Continuation Controls

Provider-native controls may help execute a bounded task, but they do not
replace vault task selection, leases, checkpoints, completion proof, or approval
boundaries.

- Claude Code `/goal` continues turn-to-turn until a completion condition is
  evaluated as satisfied.
- Claude Code `/loop` schedules repeated prompts while a session stays open.
- Codex `/goal` keeps a durable objective attached to an active thread.
- Codex app thread automations provide recurring heartbeat-style wake-ups for a
  thread when scheduled context-preserving follow-up is useful.

Use one observable outcome, one bounded slice, proof requirements, and explicit
stop conditions. Run the normal continuation preflight before claiming related
work. See [[codex-claude-goal-loop-continuation-direction]] and the compact
rules in [[continuation-operator-card]].

## Universal Budget Preflight

Every agent should use the same habit, including manually started agents:

```text
before a substantial task or new phase
-> estimate whether the work plus validation and handoff reserve fits
-> proceed, narrow the scope, checkpoint, or stop
```

Agents should leave a durable checkpoint before token, usage, time, lease, or
context limits force an abrupt shutdown.

Use provider-native headroom signals when available, but do not require them.
Unknown headroom is not unlimited headroom. Keep at least 20% of the estimated
session time or 10 minutes, whichever is larger, for validation, Activity,
lease handling, and durable handoff before starting a substantial manual phase.
Scheduled heartbeat roles should use their configured shutdown reserve and
remain stricter. See [[provider-usage-and-context-limit-direction]] and the
compact checklist in [[provider-budget-preflight-operator-card]].

## Startup Prompt

```text
Wake up as the assigned worker role.

Read AGENTS.md and the role configuration only. Inspect the eligible queue through deterministic helpers. If no eligible task exists, stop immediately without loading broad vault context.

Claim one eligible bounded task. Load only its compact work packet and linked context needed for the task. Stay within the configured time, task, cost, token, lease, and autonomy limits.

Before each substantial phase and before claiming a related or newly-unblocked continuation task, estimate whether the work, validation, and durable handoff fit inside the remaining budget with shutdown reserve. Continue only when the estimate is comfortably safe. If exact usage is unavailable or the estimate is uncertain, stop earlier and checkpoint.

Do not publish, send externally, spend money, install third-party tools, grant secret access, delete durable evidence, cross audience boundaries, or create additional agents without Leo approval.

Before stopping, validate the work, append a compact task activity update, release or renew the lease as appropriate, and emit either a completion summary, a review artifact, or an approval request.
```

## First Workers

### Capture Worker

```text
type: deterministic script
schedule: every six hours
work: run YouTube playlist capture
AI tokens: none
```

Already implemented through `launchd`.

### Transcript Review Worker

```text
type: AI heartbeat
schedule: daily
autonomy: report_only
work: scan raw/transcripts/manifest.md and propose a bounded review batch
max_tasks: 1
```

The first pilot should produce a compact report or READY task. It should not synthesize every captured transcript automatically.

### Wiki Health Worker

```text
type: deterministic scan plus reviewed repair task
schedule: weekly
autonomy: report_only
work: run delta health scan and surface actionable changes
```

Do not schedule broad automatic wiki edits.

### General Task Worker

```text
type: AI heartbeat
schedule: conservative interval
autonomy: task-defined
work: claim one eligible READY task through pick-next helper
```

Add only after deterministic dependency reconciliation, relationship reporting, and `pick-next` exist.

Start with `max_tasks: 1`. After trustworthy runs, permit a small continuation
ceiling so a warm worker can process newly-unblocked or related tasks without
paying repeated startup context costs.

## Approval Boundary

Always require Leo approval before:

- publishing or sending externally
- changing pricing, offers, public copy, or brand rules
- crossing private/public audience boundaries
- spending money
- installing third-party tools, packages, skills, or plugins
- granting or expanding secret access
- deleting durable source evidence
- creating additional autonomous workers or agents
- increasing cost, time, or frequency limits materially

## Observability

Write compact local JSONL run logs:

```text
runs/heartbeats/transcript-reviewer.jsonl
runs/heartbeats/wiki-health.jsonl
runs/heartbeats/general-worker.jsonl
```

Post to Slack only when a task completes, Leo approval is needed, a repeated failure occurs, a worker is blocked, a budget is exhausted, or a meaningful summary is due. Keep routine no-work runs silent.

## Rollout Order

1. Add a daily report-only transcript-review heartbeat.
2. Add local heartbeat configuration and JSONL logging.
3. Complete dependency reconciliation, relationship reporting, and `pick-next`.
4. Add one general task worker with `max_tasks: 1`.
5. Send meaningful summaries and approvals through Slack.
6. Add warm-session continuation with a small `max_tasks` ceiling after reviewing several trustworthy runs.
7. Expand roles, schedules, or autonomy only after reviewing several trustworthy runs.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[deterministic-automation]]
- related_to: [[multi-agent-coordination]]
- related_to: [[agent-role-registry]]
- related_to: [[task-system]]
- related_to: [[slack-agent-command-center]]
- related_to: [[youtube-transcript-workflow]]
