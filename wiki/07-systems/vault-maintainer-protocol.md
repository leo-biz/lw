---
title: Vault Maintainer Protocol
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
  - vault-maintainer
  - ai-reviewed
created: 2026-05-29
updated: 2026-05-30
---

# Vault Maintainer Protocol

## Purpose

Define the responsibilities for agents explicitly asked to maintain the Leo Life Wiki.

This is not required for every external agent. Use it only in Vault Worker mode.

Vault Workers should read [[vault-operating-model]] before making structural changes.

## Maintainer Responsibilities

- Process `raw/inbox/` using [[inbox-routing-workflow]].
- Process YouTube sources using [[youtube-transcript-workflow]].
- Preserve raw sources. Do not edit or rewrite files in `raw/` unless Leo explicitly asks.
- Do not treat `UNREVIEWED` material as settled truth.
- Prefer `HUMAN_REVIEWED` or clearly current pages for pricing, brand rules, public copy, client-facing material, and technical operating procedures.
- Keep Leo/private material separate from Sir Leo/public-facing material.
- For useful learning sources, extract an application: task, decision, practice rep, shipped output, changed routine, or experiment.
- Suggest better structure when the current structure creates friction.
- Before editing, inspect and declare live file ownership through [[file-claim-ledger]].

## Ingest Standard

When a new source, transcript, note, screenshot, or document is added:

1. Identify what it is.
2. Decide whether it belongs in `raw/`, `wiki/`, `work/`, `code/`, `exports/`, or should remain in `raw/inbox/`.
3. Preserve the source when it matters.
4. Mark it `UNREVIEWED` if it has not been processed.
5. Summarize what matters.
6. Create or update relevant wiki pages.
7. Add useful tags and typed links.
8. Flag contradictions, stale claims, and open questions.
9. Create tasks only when there is a clear outcome and definition of done.
10. Update the index, inbox, and log when appropriate.

## Review Statuses

```text
UNREVIEWED
AI_REVIEWED
HUMAN_REVIEWED
NEEDS_REVISION
ARCHIVED
SUPERSEDED
```

## Index and Log Rules

Update `index.md` when:

- adding important pages
- adding new operating areas
- adding durable entry points
- changing the map of the system

Append to `log.md` when:

- ingesting a meaningful source
- changing an important decision
- creating or changing a system workflow
- creating a meaningful export
- doing a health/lint review

Do not log tiny formatting fixes, typo fixes, or clerical noise.

## Git Rule

When Git is in use, commit finished meaningful batches with a clear message.
Do not accumulate coherent finished slices in the working tree. Use attributed
checkpoint commits through `scripts/agent_commit.py` before continuing into
another bounded phase. Use a completion commit when the assigned outcome is
finished.

Treat `index.md`, `log.md`, and current handoff pages as short-lived shared
entry-point edits: claim late, inspect first, stage selectively when needed,
commit promptly, and release the claim.

## Bulk Edit Rule

Before changing more than 20 files:

1. Inspect Git status and separate unrelated edits.
2. Prove the final format on one representative file.
3. Confirm the rendering environment when links or presentation matter.
4. Ask Leo to confirm the sample before multiplying the change.
5. Prefer a reusable script with dry-run validation for structured rewrites.
6. Validate file counts, content invariants, and exact staging scope before committing.

Preserve raw source bodies. Add metadata or navigation helpers around the source
unless Leo explicitly approves body edits.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[vault-operating-model]]
- related_to: [[inbox-routing-workflow]]
- related_to: [[learning-to-application-loop]]
- related_to: [[youtube-transcript-workflow]]
- related_to: [[task-system]]
- related_to: [[codebase-memory-workflow]]
- related_to: [[file-claim-ledger]]
