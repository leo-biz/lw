---
title: Agent Role Registry
node_type: reference
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - roles
  - coordination
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-30
---

# Agent Role Registry

## Purpose

Keep a small reusable set of agent roles while treating provider chats and threads as temporary workers.

The vault remembers the work. Provider threads are disposable execution contexts.

For substantial work, temporary threads should register lifecycle presence
through [[agent-presence-ledger]] so Leo can see who is active, waiting,
blocked, finished, or gone.

## Operating Model

```text
reusable role instructions
-> temporary provider thread
-> one scoped task or coherent batch
-> validation, activity update, commit, or handoff
-> fresh thread when the objective or role changes
```

Do not create a permanent named agent for every task. Do not keep a thread alive merely to consume its remaining context window.

Before starting a substantial task or a new phase, estimate whether execution,
validation, and a durable handoff fit within the remaining usage and context
budget. Stop early and checkpoint when the estimate is uncertain. When budget
is healthy, prefer a newly-unblocked dependent task or a closely related task
that benefits from the context already loaded.

## Reusable Roles

| Role | Use For | Typical Output |
|---|---|---|
| `vault-worker` | Ingest, synthesis, task maintenance, durable vault edits | Wiki updates, tasks, commits |
| `researcher` | Primary-source research and bounded evaluations | Research brief, recommendation, linked sources |
| `coder` | Scoped implementation in the vault or an opted-in repo | Code, tests, commit, handoff |
| `reviewer` | Independent QA, code review, safety review, acceptance checks | Findings, verification report, approval recommendation |
| `automation-worker` | Deterministic scripts and scheduled jobs | Run summary, exception report |

Start with these roles. Add another only when repeated work requires distinct instructions, tools, or approval boundaries.

Roles describe the kind of work. Capability profiles describe what a specific
worker can safely do. Follow [[worker-capability-routing]] when matching queued
tasks to providers or models.

## Thread Rules

Use one temporary provider thread for one task or coherent phase. Continue a thread while:

- the objective is unchanged
- the role still fits
- context remains compact and relevant
- the next work is a natural continuation

Start a fresh thread when:

- the assigned outcome is complete
- a different role should own the next phase
- context is noisy or difficult to summarize
- the work reaches a clean commit or handoff
- progress requires approval or a later resumption

Agents should proactively tell Leo when a fresh thread is the cleaner path:

```text
Good handoff point: start a fresh <role> thread for <task>.
```

## Manual And Dispatched Work

Current manual flow for judgment-heavy work:

```text
open provider
-> start or continue a thread
-> send compact task packet
-> agent claims task
-> agent works and records durable state
```

Target Slack-dispatched flow:

```text
Slack message
-> dispatcher creates or claims Markdown task
-> dispatcher selects reusable role and provider
-> dispatcher creates or steers temporary worker thread
-> worker records durable state
-> Slack receives status, approvals, and result
```

Deterministic scripts should run directly on schedules without creating provider chats.

AI heartbeat workers should use [[autonomous-agent-heartbeats]]. They may start
temporary provider threads only for explicitly eligible bounded tasks, and must
stop immediately when no eligible work exists.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[multi-agent-coordination]]
- related_to: [[slack-agent-command-center]]
- related_to: [[agent-system]]
- related_to: [[task-system]]
- related_to: [[autonomous-agent-heartbeats]]
- related_to: [[agent-presence-ledger]]
- related_to: [[worker-capability-routing]]
