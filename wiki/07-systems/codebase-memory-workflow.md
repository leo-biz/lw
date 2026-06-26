---
title: Codebase Memory Workflow
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: technical/internal
tags:
  - systems
  - codebase-memory
  - ai-agents
  - playbook
  - ai-reviewed
created: 2026-05-28
updated: 2026-05-28
---

# Codebase Memory Workflow

## Purpose

Create reusable repo memory for selected codebases so agents do not repeatedly spend tokens rediscovering the same architecture, commands, conventions, and known issues.

This is opt-in. Not every repo should be managed by the vault.

## Core Distinction

```text
Git repo = exact source of truth for code
code/ = reusable AI memory about selected repos
wiki/ = broader system knowledge and workflows
work/ = tasks and execution, once created
```

The vault should not copy source trees or pretend to be Git.

## What "Ingest This Repo" Means

When Leo says to ingest or manage a repo, the agent should:

1. Inspect the live repo.
2. Identify stack, structure, commands, entry points, tests, and major modules.
3. Create `code/<project-slug>/agent-brief.md`.
4. Create supporting pages only if needed.
5. Add the repo to `code/_registry/managed-repos.md`.
6. Record the current Git commit as `last_reviewed_commit`.
7. Link any relevant tasks, decisions, or outputs.
8. Append a meaningful entry to `log.md`.

## What To Capture

- What the repo is
- How to run it
- How to test it
- Main architecture
- Important files and why they matter
- Common commands
- Conventions
- Current work
- Known issues
- Things not to touch
- Reusable findings
- Last reviewed commit

## What Not To Capture

- Full source copies
- `.git`
- dependency folders
- build outputs
- caches
- secrets or `.env` values
- giant logs unless summarized

## Update Rule

Update code memory only when the agent learns something reusable:

- architecture changed
- setup commands changed
- important files moved
- conventions changed
- recurring issue discovered
- a decision affects future work
- a new common command or workflow is found

Do not update code memory for tiny edits, one-off bugs, or facts that are obvious from the current file being edited.

## Working On A Managed Repo

Before working on a managed repo:

1. Read `code/<project-slug>/agent-brief.md`.
2. Check `last_reviewed_commit` against the live repo.
3. Use source files and Git for exact truth before editing.
4. Do the requested work in the repo.
5. Update code memory only if reusable understanding changed.

## Working On An Unmanaged Repo

Work normally. Do not create code memory unless Leo asks to ingest or manage the repo.

## Staleness Rule

Code memory is a map, not the territory. If memory conflicts with source, trust source and update memory if the correction is reusable.

## Linked Nodes

- implements: [[../../code/README]]
- related_to: [[wiki-operating-rules]]
- related_to: [[sqz-context-compression]]
