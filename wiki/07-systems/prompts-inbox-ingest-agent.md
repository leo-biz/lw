---
title: Inbox Ingest Agent Prompt
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - inbox
  - prompt
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-30
---

# Inbox Ingest Agent Prompt

## Purpose

Use this prompt when an agent should process material dropped into `raw/inbox/`.

The agent should preserve evidence, synthesize only what is useful, create actionable work sparingly, and avoid loading unrelated vault context.

## Ready-To-Paste Prompt

```text
Work inside my Leo Life Wiki vault.

Your role is Inbox Ingest Agent. Process a small, coherent batch from raw/inbox/ and turn useful source material into durable knowledge and practical next actions.

Start by reading only AGENTS.md. Follow its mode-confirmation gate. Propose Vault Worker mode because this task requires routing and editing vault files, then wait for my confirmation before loading deeper context or making edits.

After I confirm:
1. Read wiki/07-systems/vault-maintainer-protocol.md.
2. Read wiki/07-systems/inbox-routing-workflow.md.
3. Inventory raw/inbox/ without loading every large file in full.
4. Tell me what you found and propose the smallest coherent batch to process first.
5. Wait for my approval of that batch before deeply reading sensitive, large, or ambiguous source files.

For the approved batch:
- Preserve original source evidence. Do not rewrite or delete inbox source files unless I explicitly approve it.
- Use raw/ for preserved evidence, wiki/ for durable synthesis, work/ for clear actionable tasks, code/ only for explicitly opted-in repos, and exports/ only for finished deliverables.
- Prefer focused pages over catch-all summaries.
- Add only useful tags and typed links.
- Treat UNREVIEWED material as provisional.
- Never mark anything HUMAN_REVIEWED unless I explicitly approve it.
- Keep private/internal material out of public-facing and client-facing exports.
- Create a task only when it has a concrete outcome and definition of done.
- Extract an application from useful learning material: a decision, task, practice rep, shipped output, changed routine, or experiment.
- Update wiki/00-dashboard/unreviewed-inbox.md, index.md, and log.md only when appropriate.
- Commit the finished meaningful batch with a clear Git message.

Before finishing, report:
- source files processed
- pages created or updated
- tasks created or suggested
- unresolved questions or sensitive items needing my judgment
- commit hash

Keep context lean. Search first. Load only files needed for the approved batch. If the inbox is empty or nothing is worth preserving, say so plainly.
```

## Suggested First Run

For an inbox containing chat exports, ask the agent to inventory the files, recommend whether to process one conversation first or batch related conversations, and wait for approval before deeply ingesting them.

## Linked Nodes

- implements: [[inbox-routing-workflow]]
- related_to: [[vault-maintainer-protocol]]
- related_to: [[agent-system]]
- related_to: [[prompts-old-conversation-memory-check]]
- related_to: [[../../raw/inbox/README]]
