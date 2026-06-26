---
title: Inbox Routing Workflow
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - inbox
  - playbook
  - ai-agents
  - ai-reviewed
created: 2026-05-29
updated: 2026-05-29
---

# Inbox Routing Workflow

## Purpose

Make Leo's capture flow simple.

Leo should not have to decide whether something belongs in `raw/`, `wiki/`, `work/`, `code/`, or `exports/`. If placement is not obvious, Leo can drop it into `raw/inbox/` and an AI agent handles routing.

## Human Rule

Put unclear material in `raw/inbox/`.

Examples:

- transcript
- screenshot
- note
- article
- idea
- task thought
- project note
- codebase note
- draft copy
- meeting note

## Agent Responsibilities

When processing `raw/inbox/`, the agent should:

1. Identify what each item is.
2. Decide whether it is source evidence, wiki knowledge, a task, codebase memory, an export, or trash/noise.
3. Preserve original source material when it matters.
4. Create or update wiki pages when synthesis is useful.
5. Create work items only when there is a clear outcome.
6. Route codebase material to `code/` only for repos Leo has opted into.
7. Flag private/public boundary risks.
8. Update `wiki/00-dashboard/unreviewed-inbox.md` when review is needed.
9. Update `index.md` and `log.md` for meaningful changes.

## Routing Rules

### Send To `raw/`

Use when the item is evidence that should be preserved:

- transcript
- article
- PDF
- screenshot
- meeting note
- chat export
- source document

Do not rewrite source evidence. If cleanup is needed, create a separate wiki page.

### Send To `wiki/`

Use when the item should become durable understanding:

- concept
- decision
- playbook
- source summary
- offer note
- brand rule
- system rule
- current-state page

### Send To `work/`

Use when the item is actionable:

- draft something
- build something
- review something
- research something
- follow up
- validate an idea

Tasks should have a clear outcome and definition of done.

### Send To `code/`

Use only for opted-in managed repos.

If Leo says "ingest this repo," follow [[codebase-memory-workflow]].

### Send To `exports/`

Use when the item is a finished or deliverable artifact, or when a wiki/work task produces one.

Do not place private/internal material into public or client-facing exports without explicit instruction.

### Leave In `raw/inbox/`

Leave the item in `raw/inbox/` when:

- its meaning is unclear
- it needs Leo's judgment
- it may be sensitive
- there is no safe routing decision yet

Add a note in `wiki/00-dashboard/unreviewed-inbox.md` explaining what Leo should clarify.

## Decision Prompt For Agents

For each inbox item, ask:

```text
Is this evidence, knowledge, work, code memory, or an output?
Does it need preservation, synthesis, execution, review, or deletion?
What is the smallest useful next move?
```

## Linked Nodes

- implements: [[vault-operating-model]]
- related_to: [[prompts-inbox-ingest-agent]]
- related_to: [[../00-dashboard/unreviewed-inbox]]
- related_to: [[../../raw/inbox/README]]
