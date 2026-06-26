---
title: ChatGPT Archive Review Thread Handoff Prompt
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - chatgpt-export
  - archive-review
  - prompts
  - handoff
created: 2026-05-30
updated: 2026-05-30
---

# ChatGPT Archive Review Thread Handoff Prompt

## Purpose

Let a fresh temporary provider thread continue archive review from durable packet state instead of rereading completed raw chunks.

## Ready-To-Paste Prompt

```text
Work with me on my Leo Life Wiki vault.

Read AGENTS.md first and follow its mode-confirmation gate.

After I confirm Vault Worker mode, read:
- wiki/07-systems/chatgpt-archive-selective-review-workflow.md
- the assigned work task
- the latest checkpoint for the assigned batch
- the current conversation rollup if one exists
- only the next bounded packet or packets assigned to this thread

Continue from next_packet. Do not reread completed raw chunks unless the checkpoint identifies a specific uncertainty. Preserve raw source bodies. Use sqz for repeated or large reads when available.

Before the thread becomes context-heavy, finish the current packet and save:
- chunk summary
- updated conversation rollup when applicable
- compact checkpoint with last_completed_packet and next_packet
- task activity update

Stop at the task's approval boundary. Do not apply brand, pricing, offer, or private-boundary changes without Leo review.
```

## Linked Nodes

- implements: [[chatgpt-archive-selective-review-workflow]]
- related_to: [[multi-agent-coordination]]
- related_to: [[agent-role-registry]]
