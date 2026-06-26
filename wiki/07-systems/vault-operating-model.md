---
title: Vault Operating Model
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
created: 2026-05-29
updated: 2026-05-30
---

# Vault Operating Model

## Purpose

This page is the plain-English overview of how Leo Life Wiki works.

The vault is a file-native operating system for personal knowledge, AI-assisted work, codebase memory, and reusable outputs. Obsidian is the viewer. The markdown files are the system.

## Core Flow

```text
raw/inbox -> AI routing -> raw / wiki / work / code / exports
                             |
                             v
                    decisions, links, memory, and reusable understanding
```

The goal is not to collect notes. The goal is to turn sources and conversations into better decisions, faster application, finished assets, and less repeated rediscovery.

## Main Areas

### `raw/inbox/`

Single capture drop zone.

Use when Leo does not want to decide where something belongs. An AI agent should route inbox items into the right place.

Rules:

- Leo can drop unclear material here as the single source of input.
- Agents classify, route, preserve, summarize, task, or flag for review.
- If routing is unclear or sensitive, leave the item in `raw/inbox/` and add a review note.

### `raw/`

Preserved evidence.

Use for transcripts, documents, screenshots, notes, source material, and other inputs that should not be overwritten casually.

Rules:

- Preserve raw files.
- Mark unprocessed material as `UNREVIEWED` when useful.
- Do not treat raw or unreviewed material as settled truth.
- Do not rewrite raw files unless Leo explicitly asks.
- Preservation and Git tracking are separate decisions. Follow [[wiki-operating-rules#Raw Source Git Policy|Raw Source Git Policy]] before committing or pushing raw evidence.

### `wiki/`

Living synthesis.

Use for cleaned-up knowledge, decisions, playbooks, concepts, summaries, dashboards, and operating rules.

Rules:

- Prefer focused pages over giant catch-all pages.
- Use review status to show trust level.
- Link pages when the relationship helps future reasoning.
- Keep current decisions separate from old ideas and experiments.

### `work/`

Task and execution pipeline.

Use for actual work items that need to move through status folders:

```text
inbox -> ready -> in-progress -> review -> done
```

Other statuses:

```text
blocked
someday
```

Rules:

- Each meaningful task should be its own markdown file.
- Tasks should have a clear outcome and definition of done.
- Agents claim tasks before working.
- Public-facing, client-facing, pricing-related, or private-boundary tasks require Leo review.

### `code/`

Reusable codebase memory.

Use for selected repos Leo explicitly opts into. This area stores repo understanding, not source code.

Rules:

- Git repos remain the source of truth for code.
- Do not copy full source trees into the vault.
- Before working on a managed repo, read its `code/<project>/agent-brief.md`.
- Update code memory only when reusable understanding changes.

### `exports/`

Finished or deliverable outputs.

Use for polished artifacts created from the wiki:

- public copy
- client-facing documents
- team SOPs
- private briefs
- strategy drafts
- guides
- scripts
- templates

Rules:

- Do not move private/internal material into public or client-facing exports without explicit instruction.
- Public and client-facing exports should be checked against current, reviewed source material.

## Control Files

### `AGENTS.md`

Short entry point for any AI agent that touches or consults the vault.

Agents should read this first to decide whether they are in Search-Only Context, Vault Worker, External Work, or Ask Leo mode, then load only the matching protocol.

### `CLAUDE.md`

Claude-specific runtime/tool rules only.

Universal rules belong in `AGENTS.md`, not in agent-specific files.

### `index.md`

The main map.

Use it to find important pages and entry points.

### `log.md`

Meaningful chronological history.

Use it for important ingests, decisions, exports, system changes, and reviews. Do not log tiny formatting edits or clerical noise.

## Review Statuses

```text
UNREVIEWED
AI_REVIEWED
HUMAN_REVIEWED
NEEDS_REVISION
ARCHIVED
SUPERSEDED
```

Important rules:

- `UNREVIEWED` means provisional.
- `AI_REVIEWED` means processed by AI but not approved by Leo.
- `HUMAN_REVIEWED` requires explicit Leo approval.
- `SUPERSEDED` means replaced by a newer version.

## Public vs Private Boundary

The vault may contain private strategy, personal reflection, business plans, and public-facing assets. The boundary matters.

Default audience values:

```text
private/internal
public-facing
team-facing
client-facing
technical/internal
archive
```

Never assume private strategy is safe for public export.

## Learning to Application

Useful learning should produce application, not just notes.

When processing a source, look for:

- a task
- a decision
- a practice rep
- a shipped output
- a changed routine
- a business experiment
- a reusable asset

If a source does not change anything, it may belong as reference or archive instead of active work.

## When To Touch The Vault

Use the vault when something should survive the conversation:

- decisions
- sources worth preserving
- reusable workflows
- tasks or backlog items
- Sir Leo brand/offers/pricing
- codebase memory
- polished outputs
- useful summaries and syntheses

Skip the vault for quick questions, throwaway brainstorming, tiny clarifications, or ideas Leo does not want formalized yet.

If something should survive but Leo does not know where it belongs, use `raw/inbox/`.

## Memory Checks

A memory check is a lightweight review of a conversation or work session.

Use `memory check` or `mem check` when an agent should decide whether anything is worth preserving. If something has future utility, the agent should produce a Vault Handoff. If not, it should say nothing needs saving.

Memory checks are useful for external agents that are not supposed to edit the vault directly.

External agents may still use the vault as searchable context. Search-only access is different from vault maintenance: the agent can read relevant pages to become aware, but should not edit vault files unless explicitly put in Vault Worker Mode.

To reduce context usage, agents should propose the selected mode, explain why, wait for Leo's confirmation, and then load only the specific protocol page needed for that mode. If the mode is unclear, they should use Ask Leo mode.

## Suggested Agent Flow

1. Read `AGENTS.md`.
2. Read `index.md`.
3. Identify whether the request is about sources, wiki knowledge, work tasks, codebase memory, or exports.
4. If editing the vault, use [[vault-maintainer-protocol]].
5. If the request starts from `raw/inbox/`, use [[inbox-routing-workflow]].
6. Use the relevant system page.
7. Make the smallest useful update.
8. Update `index.md` and `log.md` only when the change is meaningful.
9. Commit finished batches when Git is in use.

## Key Pages

- [[../../AGENTS|AGENTS]]
- [[../../index|Index]]
- [[../../log|Log]]
- [[../00-dashboard/home|Home]]
- [[wiki-operating-rules]]
- [[agent-system]]
- [[vault-maintainer-protocol]]
- [[search-only-context-protocol]]
- [[external-work-protocol]]
- [[ask-leo-protocol]]
- [[inbox-routing-workflow]]
- [[learning-to-application-loop]]
- [[task-system]]
- [[codebase-memory-workflow]]
- [[sqz-context-compression]]
- [[../../work/README|Work README]]
- [[../../code/README|Codebase Memory]]

## Linked Nodes

- implements: [[wiki-operating-rules]]
- related_to: [[agent-system]]
- related_to: [[vault-maintainer-protocol]]
- related_to: [[learning-to-application-loop]]
- related_to: [[task-system]]
- related_to: [[codebase-memory-workflow]]
- related_to: [[../../AGENTS]]
