---
title: External Work Protocol
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - playbook
  - external-work
  - ai-reviewed
created: 2026-05-29
updated: 2026-05-29
---

# External Work Protocol

## Use When

Use this when the agent is doing work outside the vault: coding, research, drafting, debugging, planning, experiments, or tool use.

## Rules

- Do the requested work outside the vault.
- Use vault context only if it helps.
- Do not edit vault files.
- If vault context is needed, use [[search-only-context-protocol]].
- You do not need the full vault operating model unless Leo asks you to maintain the vault.
- At the end, run a memory check only if something durable may be worth preserving.

## Memory Check Output

If worth saving, produce a Vault Handoff using [[agent-system]].

If not worth saving, say:

```text
Memory check: nothing worth saving.
```

## Linked Nodes

- implements: [[agent-system]]
- part_of: [[agent-system]]
- related_to: [[search-only-context-protocol]]
