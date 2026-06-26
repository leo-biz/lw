---
title: Wiki Operating Rules
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - playbook
  - ai-agents
  - ai-reviewed
created: 2026-05-21
updated: 2026-05-30
---

# Wiki Operating Rules

## Purpose

This vault is a living, compounding wiki. Raw sources are preserved. Wiki pages synthesize and connect knowledge. Outputs are generated from reviewed material.

## Core Rule

Prefer useful synthesis over perfect filing. Structure should help retrieval, decisions, and future action.

## Source Handling

- Preserve raw sources when possible.
- Mark unprocessed material as `UNREVIEWED`.
- Do not treat `UNREVIEWED` sources as settled truth.
- Prefer reviewed/current pages for pricing, brand rules, public-facing copy, client-facing exports, and technical operating procedures.

## Raw Source Git Policy

Preserving a raw source does not automatically mean committing it to Git.

- Commit normalized, durable raw evidence when it improves traceability, reproducibility, or future retrieval.
- Do not commit bulky, redundant, replaceable, temporary, or generated source artifacts by default.
- Keep secrets out of Git.
- Treat sensitive personal exports as an explicit decision: commit only when the repository storage and backup model are appropriate for that material.
- Review the privacy boundary before adding or pushing a remote. Git history is durable and difficult to scrub cleanly later.
- Use encrypted backup storage for excluded raw evidence when preservation still matters.

## Codebase Memory

- Git repos remain the source of truth for code.
- `code/` stores reusable AI memory for repos Leo explicitly opts in.
- Do not copy full source trees into the vault.
- Before working on a managed repo, read its `code/<project>/agent-brief.md`.
- Update code memory only when reusable understanding changes.

## Page Handling

- Prefer focused pages over giant catch-all notes.
- Use frontmatter when it helps search, Dataview, review, or maintenance.
- Use 3-7 useful tags per page.
- Use typed links when the relationship matters.
- Create decision pages for important choices.
- Split pages when they become too mixed.

## Bulk Edit Preflight

Before changing more than 20 files:

1. Inspect Git status and identify unrelated edits.
2. Test the final format on one representative file.
3. Verify the result in the actual rendering environment when links, layout, or presentation matter.
4. Get Leo confirmation before multiplying the change across the vault.
5. Prefer a reusable script with a dry-run mode for repeated or structured rewrites.
6. Validate file counts, expected diffs, and staging scope before committing.

For raw evidence:

- Preserve the source body. Add metadata or navigation helpers without rewriting source content.
- If body edits are necessary, make them explicit and validate that transcript or source content did not drift.
- Keep temporary extraction artifacts and replaceable source files outside the commit unless they are deliberately retained.

## Review Statuses

```text
UNREVIEWED
AI_REVIEWED
HUMAN_REVIEWED
NEEDS_REVISION
ARCHIVED
SUPERSEDED
```

## Audience Boundary

Always preserve the boundary between:

- private/internal
- public-facing
- team-facing
- client-facing
- technical/internal
- archive

Never move private strategy or personal reflection into public-facing exports without explicit review.

## Maintenance Checks

Periodically review for:

- contradictions
- stale claims
- old ideas presented as current
- missing links
- duplicate pages
- inconsistent tags
- unreviewed files piling up
- AI-reviewed pages waiting for Leo
- pages needing revision
- public/private boundary issues
- topics that deserve dedicated pages

## AI Collaboration Rule

The AI should suggest improvements, challenge weak structures, simplify rigid systems, clarify vague areas, flag contradictions, and call out when Leo is collecting too much without deciding what matters.

## Linked Nodes

- implements: [[../../AGENTS]]
- related_to: [[../00-dashboard/unreviewed-inbox]]
- related_to: [[codebase-memory-workflow]]
- related_to: [[../../index]]
