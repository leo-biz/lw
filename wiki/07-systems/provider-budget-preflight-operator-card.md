---
title: Provider Budget Preflight Operator Card
node_type: reference
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - usage-limits
  - context-windows
  - budgets
  - preflight
  - operator-card
  - ai-reviewed
created: 2026-06-08
updated: 2026-06-08
---

# Provider Budget Preflight Operator Card

Run this preflight before starting a substantial task phase and before claiming
a related or newly-unblocked continuation task. The goal is a conservative
honest estimate — not an attempt to maximize context use.

See [[provider-usage-and-context-limit-direction]] for the full direction,
limit-type taxonomy, and open questions.

## Preflight Checklist

```text
task or phase:                   [name of the work being evaluated]
bounded outcome:                 [single coherent result that completes this phase]
estimated execution time:        [conservative wall-clock estimate]
validation and handoff reserve:  [time needed after execution: proof, Activity, lease, checkpoint]
lease time remaining:            [from task lease expiry]
context headroom signal:         [from provider-native status if available; else "unknown"]
subscription or API headroom:    [from provider-native status if available; else "unknown"]
cost allowance signal:           [session spend limit or budget, if configured; else "unknown"]
approval boundary:               [anything that needs Leo sign-off before proceeding]
can this finish or checkpoint safely with margin:  [YES / NO / UNCERTAIN → stop if uncertain]
```

**Unknown headroom is not unlimited headroom.** If any signal is absent, treat
it as a conservative constraint and stop or narrow the scope rather than
proceeding on an optimistic assumption.

## Provider-Native Inputs (Optional)

These are inputs to the preflight, not a portable contract. They may reset on
resume and are not available from all providers. Use them when present; do not
require them.

### Codex CLI

```bash
/status   # session configuration, token usage, remaining context capacity
```

`ccusage codex daily`, `ccusage codex session` — local token/session
accounting from usage logs (does not prove provider-side remaining allowance).

### Claude Code

```bash
/usage    # session token consumption
/cost     # session spend (API-key sessions)
```

`rate_limits` custom status-line fields expose active rate-limit signals.
`ccusage claude daily`, `ccusage claude session`, `ccusage claude blocks --active`
— local token/session accounting.

### Anthropic API Response Headers

```text
anthropic-ratelimit-requests-remaining
anthropic-ratelimit-tokens-remaining
anthropic-ratelimit-input-tokens-remaining
anthropic-ratelimit-output-tokens-remaining
retry-after
```

These are observable at the API client layer. Do not store values in the vault.
Log them transiently in the session if the runner supports it.

### OpenAI API Response Headers

```text
x-ratelimit-remaining-requests
x-ratelimit-remaining-tokens
x-ratelimit-reset-requests
x-ratelimit-reset-tokens
```

Same guidance: observable at the client layer, do not store in the vault.

## Reserve Rule

Keep at least **20% of the estimated session time or 10 minutes, whichever is
larger**, for validation, Activity stamp, lease handling, and durable handoff
before starting a substantial phase.

Scheduled heartbeat roles must use their configured `shutdown_reserve_minutes`
and remain stricter than the 20% / 10-minute floor.

## Operating Rules

1. **Unknown headroom is not unlimited headroom.** Treat absent signals as
   conservative constraints.
2. Prefer one bounded coherent slice. Do not start a new task to use remaining
   context.
3. Keep at least 20% session time or 10 minutes (whichever is larger) as
   validation and handoff reserve.
4. Checkpoint before loading another large context packet, starting a broad
   test suite, or claiming a related task.
5. Stop rather than continue when the estimate is uncertain.

## When to Stop vs Continue

| Signal | Action |
|---|---|
| All estimates fit with margin | Continue |
| Uncertain or missing headroom signal | Stop and checkpoint |
| Remaining time < validation + handoff reserve | Stop and checkpoint |
| Next task is outside the current workstream | Stop; let Leo or the queue assign it |
| `max_tasks` ceiling reached | Stop unconditionally |

## Preflight for Continuation

Before claiming a related or newly-unblocked task after completing a slice:

```text
finish and prove the current bounded slice
-> checkpoint-commit with attribution
-> close or renew the task lease
-> run this preflight for the candidate next task
-> continue only when the checklist result is YES with margin
-> otherwise stop with a durable handoff note
```

## Limit Types Quick Reference

| Limit | What it governs |
|---|---|
| Subscription allowance | Included product usage over a rolling or weekly window |
| API rate limit | Requests or tokens per short interval |
| API spend limit | Maximum billable use over a billing period |
| Context window | Maximum tokens one model request can carry |
| Output-token limit | Maximum tokens one model response can produce |
| Runtime session limit | Tool-specific cap, expiry, or interruption boundary |

These limits are independent. Remaining context does not imply remaining
subscription allowance, API throughput, spend budget, or runtime time.

## Linked Nodes

- direction: [[provider-usage-and-context-limit-direction]]
- implements: [[autonomous-agent-heartbeats]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[continuation-operator-card]]
- related_to: [[agent-completion-proof-protocol]]
- related_to: [[agent-presence-ledger]]
