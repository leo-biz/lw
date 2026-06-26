---
title: Ask Leo Protocol
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
  - ask-leo
  - ai-reviewed
created: 2026-05-29
updated: 2026-05-29
---

# Ask Leo Protocol

## Use When

Use this when the agent cannot safely choose a mode or proceed without Leo's judgment.

## Ask Before

Ask Leo before:

- editing the vault when the request may only need search-only context
- routing sensitive material
- changing public-facing or client-facing exports
- marking anything `HUMAN_REVIEWED`
- creating codebase memory for a repo not explicitly opted in
- changing pricing, brand rules, or current decisions
- deleting, archiving, or superseding meaningful material

## How To Ask

Keep it short. State the uncertainty and the needed choice.

Format:

```text
Mode unclear: <brief reason>.
Do you want me to use <mode A> or <mode B>?
```

If the agent has a likely mode but needs confirmation, use:

```text
Proposed mode: <mode> because <reason>.
Please confirm before I continue.
```

## After Leo Answers

Confirm the selected mode, load only that mode's protocol, and continue.

## Linked Nodes

- implements: [[agent-system]]
- part_of: [[agent-system]]
- related_to: [[vault-maintainer-protocol]]
- related_to: [[search-only-context-protocol]]
- related_to: [[external-work-protocol]]
