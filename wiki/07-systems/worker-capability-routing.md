---
title: Worker Capability Routing
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - routing
  - models
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Worker Capability Routing

## Purpose

Route queued work to an appropriate worker without hardcoding every task to one
provider or assuming an agent knows facts its runtime does not expose.

Use reusable roles for the kind of work. Use capability profiles for what the
current worker can safely and efficiently do.

## Truthful Worker Profile

A dispatcher, scheduled worker config, or manually started agent should provide
or report what is actually known:

```yaml
provider: openai
model: gpt-5-codex
role: coder
strengths:
  - code
  - debugging
  - repo-navigation
  - tests
tools:
  - shell
  - git
  - sqz
cost_tier: high
context_tier: large
autonomy: execute_internal
```

Do not invent the exact model, cost, remaining usage, context allowance, or tool
availability. Use `unknown` when the runtime does not expose a fact.

## Task Requirements

Add optional task metadata only when routing materially benefits:

```yaml
worker_role: coder
capability_requirements:
  - code
  - tests
model_tier: standard
preferred_cost_tier: low
verification_commands:
  - python3 -m unittest scripts.tests.test_example -v
```

Use `model_tier` as a minimum reasoning or quality floor:

```text
economy    routine classification, extraction, tagging, queue scans
standard   bounded research, wiki synthesis, normal code changes
advanced   ambiguous architecture, strategy, high-risk reasoning, complex review
```

## Selection Order

When choosing among eligible workers:

1. satisfy required tools, capability requirements, role, and approval boundary
2. satisfy the minimum model tier
3. prefer the lowest-cost worker that safely fits
4. prefer warm context for newly-unblocked or related work when budget allows
5. route complex or high-risk work upward rather than silently lowering quality
6. use an independent reviewer when blast radius or ambiguity justifies it

## Typical Fit

| Worker Shape | Prefer |
|---|---|
| Deterministic script | Predictable polling, reconciliation, scans, rotation |
| Economy model | Triage, tagging, queue scans, routine extraction |
| Coding agent | Implementation, tests, debugging, repo navigation |
| Advanced reasoning model | Architecture, strategy, ambiguous synthesis, high-risk review |
| Reviewer role | Independent QA, acceptance checks, boundary review |

Stronger workers may take simpler work when idle. Weaker workers should not
silently claim tasks above their declared floor.

## Queue Packet Rule

The compact task packet should include:

```text
worker role and capability requirements
minimum model tier
required tools
verification commands
approval boundary
```

Until automated routing exists, a fresh worker should compare the task
requirements to its truthful profile and skip tasks it cannot safely complete.

## Escalation Gate

Cheap (economy) models should handle report-only review, triage, and
classification before escalating to a coding agent or advanced model. A
full worker should only be invoked when the economy pass identifies a
finding that genuinely requires action — not for every queue item by default.

Apply this gate to: queue scan decisions, transcript triage, inbox
classification, audit report generation, and any workflow where the first
pass result is a list or report rather than a code change.

## Linked Nodes

- implements: [[agent-role-registry]]
- related_to: [[task-system]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[llm-routing-and-token-reduction]]
