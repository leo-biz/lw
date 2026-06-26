---
title: Slack Agent Command Center
node_type: hypothesis
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - slack
  - automation
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-31
---

# Slack Agent Command Center

## Purpose

Use Slack as Leo's human-facing surface for dispatch, approvals, replies, and meaningful alerts across different AI providers and sessions.

Slack is a communication interface, not the durable system of record.

Use [[agent-control-plane-operating-model]] for the shared definitions of chat
mode, task mode, worker mode, sessions, memory, LiteLLM routing, BriefKit
workers, and authority boundaries.

## Minimal Pilot

```text
Slack message
-> dispatcher
-> create or claim Markdown task
-> construct compact work packet
-> assign one worker
-> post status
-> request approval when needed
-> write durable result to vault
```

Start with one dependable dispatcher and one approvals loop. Delay a large autonomous agent organization until the pilot reveals real friction.

The dispatcher should select from a small reusable role registry, then create or steer temporary provider threads only when judgment-heavy work needs an AI worker. Deterministic scripts should run directly without provider chats.

## Approved Pilot Architecture

Approved by Leo on 2026-05-31. Build a narrow custom local bridge before adding
any provider-specific worker automation:

```text
Slack Socket Mode
-> local dispatcher process
-> Markdown task adapter
-> existing task lease helper
-> compact packet builder
-> Slack status and approval replies
```

Use one Slack app and one local dispatcher process. Keep Slack app tokens outside
the vault under `~/.config/leo-life/slack/`. Keep Markdown tasks in `work/` as
the source of truth and use `scripts/task_lease.py` for claim transitions rather
than creating a second lease system.

Split the pilot into two bounded slices:

1. Implement the Slack-to-vault core: mention handling, task creation or claim,
   compact packets, status replies, approval prompts, reaction handling, and
   durable approval activity entries.
2. Add one provider adapter only after Leo selects the first provider and
   approves its execution boundary. The adapter should create or steer a
   temporary worker thread where supported and record the real session ID,
   provider, and lease on the Markdown task.

The dispatcher core should expose a small worker-adapter boundary so a later
Hermes comparison or another provider integration does not change Slack event
handling or Markdown persistence. Do not install Paperclip or Hermes for the
pilot.

## Approved Event Boundary

Start with:

```text
app_mention     create or claim a task, or respond with scoped help
reaction_added  approve or reject a dispatcher approval prompt
```

Configure the minimum matching Slack surface:

```text
bot scopes:       app_mentions:read, chat:write, reactions:read
bot events:       app_mention, reaction_added
app-level scope:  connections:write
```

Add public-channel thread replies as the next permission increment after the
mention-and-reaction path works:

```text
bot scope:   channels:history
bot event:   message.channels
```

Filter `message.channels` aggressively: accept only replies in dispatcher-owned
threads and ignore routine channel traffic. If the pilot later needs private
channels or direct messages, add their history scopes and message events
separately rather than requesting them upfront.

Persist task creation, claims, meaningful state changes, consequential
approvals, rejections, and selected changes. Keep help responses, malformed
commands, duplicate event handling, and routine acknowledgements transient.

## Next Approval Gate

Architecture approval was recorded on 2026-05-31. Before implementation
continues, Leo should:

- create or authorize the Slack app
- provision tokens outside the vault
- select the first provider adapter before the second rollout slice

## Suggested Channels

```text
#ai-general
#ai-approvals
#ai-activity
#sir-leo
#tech-projects
```

Channels should represent attention boundaries and domains, not individual agents.

## Approval UX

Prefer:

```text
thumbs up reaction = approve
thumbs down reaction = reject
thread reply = changes, answer, or selected option
```

Record consequential approvals back into the vault task or decision page.

## Context Engineering

The dispatcher should send compact work packets, not entire conversations:

```text
task
owner
definition of done
relevant links
recent activity
approval boundary
output destination
```

Changing providers should not mean replaying a large thread.

## What Slack Should Not Do

- replace Markdown tasks
- become permanent memory
- run deterministic jobs through an AI model
- receive noisy logs for every script execution
- broadcast every agent thought

## Open Questions

- Should a later [[hermes-agent-runtime-evaluation|Hermes]] comparison remain separate or provide an optional worker adapter after the narrow custom pilot?
- When does [[paperclip-agent-orchestration-evaluation|Paperclip]] or another orchestration UI become useful enough to justify a second control plane?
- Which provider adapter should be evaluated first after the Slack-to-vault core?

## Linked Nodes

- implements: [[multi-agent-coordination]]
- related_to: [[agent-control-plane-operating-model]]
- related_to: [[task-dashboard]]
- related_to: [[deterministic-automation]]
- related_to: [[agent-role-registry]]
- related_to: [[hermes-agent-runtime-evaluation]]
- related_to: [[paperclip-agent-orchestration-evaluation]]
