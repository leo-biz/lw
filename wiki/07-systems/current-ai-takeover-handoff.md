---
title: Current AI Takeover Handoff
node_type: reference
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - handoff
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-31
---

# Current AI Takeover Handoff

## Purpose

Give a fresh AI session a small routing page. This is not a system manual and
should not repeat durable rules already maintained elsewhere.

Start with `AGENTS.md`. After Leo confirms the proposed mode, use only the
smallest relevant path below.

## Selective Start

### New Or Unrelated Work

If Leo gives a clear new task, skip recent-work recovery. Load the confirmed
mode protocol and search only the pages relevant to the request.

### Continue A Known Task

If Leo names an existing task, read that task file first. Load its checkpoint,
recent Activity, and directly linked pages only as needed.

### Recover Interrupted Or Ambiguous Work

Use the report-only takeover packet when a session stopped unexpectedly, a
provider changed mid-task, Leo asks what happened recently, or dirty files make
ownership unclear:

```bash
python3 scripts/recent_work_packet.py
python3 scripts/file_claims.py status
```

Follow [[recent-work-takeover-packet]]. Treat the packet as a retrieval map, not
permission to bulk-read recent work.

### Choose Available Work

If Leo asks an agent to pick up a task from the queue, follow
[[queue-worker-bootstrap]]. Inspect the task system rather than relying on a
priority list copied into this page:

- [[task-system]]
- [[task-dashboard]]
- `work/ready/`
- `work/in-progress/`
- `work/blocked/`

## Relevant Entry Points

Load only the entry points needed for the request:

| Need | Entry Point |
|---|---|
| Maintain the vault | [[vault-maintainer-protocol]] |
| Use vault context without edits | [[search-only-context-protocol]] |
| Work outside the vault | [[external-work-protocol]] |
| Clarify mode or boundary | [[ask-leo-protocol]] |
| Understand the overall vault | [[vault-operating-model]] |
| Coordinate multiple workers | [[multi-agent-coordination]] |
| Declare dirty-file ownership | [[file-claim-ledger]] |
| Pick up queued work | [[queue-worker-bootstrap]] |
| Resume interrupted work | [[recent-work-takeover-packet]] |
| Run bounded autonomous workers | [[autonomous-agent-heartbeats]] |
| Use Slack dispatch | [[slack-agent-command-center]] |
| Process YouTube sources | [[youtube-transcript-workflow]] |
| Review the ChatGPT archive | [[chatgpt-archive-selective-review-workflow]] |
| Manage opt-in codebase memory | [[codebase-memory-workflow]] |

## Ready-To-Paste Prompt

```text
Work with me on my Leo Life Wiki vault.

Read only AGENTS.md first. Propose the smallest appropriate mode, state your
reason, and wait for my confirmation before loading deeper context or editing.

After confirmation, use wiki/07-systems/current-ai-takeover-handoff.md as a
selective router. Load only the pages needed for my specific request. Do not
load recent work unless this is a continuation, recovery, or ownership question.
```

## Maintenance Rule

Keep this page thin. Link durable protocols instead of copying them. Do not add
rolling priority lists, implementation histories, secret paths, or large system
summaries here.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[vault-operating-model]]
- related_to: [[multi-agent-coordination]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[recent-work-takeover-packet]]
