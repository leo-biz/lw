---
title: Queue Worker Copy-Paste Prompt
node_type: reference
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - prompt
  - tasks
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Queue Worker Copy-Paste Prompt

Use this when starting a fresh Claude, Codex, ChatGPT, Grok, or other capable
agent session and you want it to pick up useful queued work.

## Copy This

```text
Read AGENTS.md and follow its mode-confirmation gate. After confirmation, follow
wiki/07-systems/queue-worker-bootstrap.md. Pick up the next eligible queued task,
claim it, load only its compact packet and required policy links, use sqz for
repeated or large reads when available, complete one bounded coherent slice,
validate it, checkpoint-commit with attribution, and continue into related work
only if budget preflight says it is safe.
```

## Point An Agent Here

```text
Read wiki/07-systems/prompts-queue-worker.md and follow the prompt under
"Copy This."
```

## Linked Nodes

- implements: [[queue-worker-bootstrap]]
- related_to: [[current-ai-takeover-handoff]]
