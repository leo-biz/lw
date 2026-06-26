---
title: Decision Memory
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - playbook
  - decisions
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Decision Memory

## Purpose

For important decisions, create a dedicated decision page so the choice, reasoning, and history don't get lost in conversation context or buried in raw sources.

## When to Create a Decision Page

- Sir Leo pricing, offers, or branding
- Event structures or CRM automations
- Business ideas moved to active pursuit
- Tech career direction changes
- Learning priorities
- Fitness plan changes
- Any decision that would be expensive to re-derive later

## Format

```markdown
---
title: Decision Title
node_type: decision
domain: [sir-leo | tech-career | business | systems | personal]
status: AI_REVIEWED
audience: private/internal
tags:
  - decision
  - [domain]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

## Summary

One sentence: what was decided.

## Current Decision

The active choice, stated clearly.

## Why

Reasoning behind the decision. Context that would otherwise be forgotten.

## Source

Link to the raw source or conversation that produced this decision.

## Old Versions

Previous versions of this decision, with dates.

## Supports

Pages or ideas this decision enables or validates.

## Contradicts

Pages or ideas this decision overrides or conflicts with.

## Open Questions

What remains unresolved.

## Next Action

What happens next because of this decision.

## Review Status

When this should be revisited.
```

## Linked Nodes

- related_to: [[wiki-operating-rules]]
- related_to: [[vault-operating-model]]
- source: [[../../raw/documents/vault-design-original]]
