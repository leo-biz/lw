---
title: Agent System
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
  - memory-check
  - ai-reviewed
created: 2026-05-29
updated: 2026-05-29
---

# Agent System

## Purpose

Define how different AI agents should interact with Leo Life Wiki, including agents that are not meant to work directly inside the vault.

Not every agent needs full vault context. Some agents should edit the vault. Some should use it as searchable context. Others should work elsewhere and produce a small handoff only if something is worth remembering.

Provider threads are temporary execution contexts. Use the compact reusable roles in [[agent-role-registry]], and proactively recommend a fresh role-specific thread when a task or coherent phase ends, the role changes, or context becomes noisy.

## Agent Modes

Before loading a detailed mode protocol or editing the vault, the agent should state the proposed mode and reason, then wait for Leo's confirmation.

```text
Proposed mode: <mode> because <reason>.
Please confirm before I continue.
```

### Vault Worker Mode

Use this when the agent is expected to edit the vault.

Detailed rules: [[vault-maintainer-protocol]]

Flow:

```text
read AGENTS.md only
propose mode and wait for Leo confirmation
read vault-maintainer-protocol.md
read current-ai-takeover-handoff.md as a selective router when needed
read queue-worker-bootstrap.md when asked to pick up queued work
edit raw/wiki/work/code/exports
update index/log if meaningful
checkpoint-commit attributed coherent slices
```

Use for:

- processing `raw/inbox/`
- ingesting sources
- updating wiki pages
- creating work tasks
- maintaining codebase memory
- producing exports
- updating system workflows

### External Work Mode

Use this when the agent is doing work outside the vault.

The agent does not need to edit the vault. It may search or read relevant vault pages when background context would improve the work, then run a memory check only if the work produced something with future value.

Detailed rules: [[external-work-protocol]]

Use for:

- coding in another repo
- research
- drafting
- debugging
- planning
- experiments
- tool use outside the vault
- quick conversations

### Search-Only Vault Context

Use this when an external agent needs awareness from the vault but should not change vault files.

Detailed rules: [[search-only-context-protocol]]

Flow:

```text
read AGENTS.md only if needed
propose mode and wait for Leo confirmation when using vault context
search index.md and relevant wiki/code/work pages
use the vault as context
do the external work
do not edit the vault
produce a Vault Handoff only if something should be saved
```

Use for:

- checking Sir Leo brand context before drafting elsewhere
- checking codebase memory before working in a live repo
- checking prior decisions before planning
- checking task context before doing external work
- avoiding repeated explanation

Rules:

- Prefer `index.md` as the map.
- Prefer reviewed/current pages.
- Treat `UNREVIEWED` material as provisional.
- Do not modify vault files unless explicitly put in Vault Worker Mode.
- If the agent learns something worth saving, produce a Vault Handoff instead of editing the vault.
- If exact wording matters, verify against the source page or source file.

### Ask Leo Mode

Use this when the agent cannot safely choose a mode, scope, destination, or safety boundary.

Detailed rules: [[ask-leo-protocol]]

Ask Leo before loading extra context or editing when the request is ambiguous.

## Memory Check

`memory check` or `mem check` means:

```text
Review this conversation or work.
Decide if anything is worth preserving.
If yes, produce a Vault Handoff.
If no, say nothing needs saving.
```

Do not save everything. Only preserve items with future utility.

## When To Run A Memory Check

Run a memory check when:

- Leo explicitly says `memory check` or `mem check`
- a decision was made
- a task was created or implied
- a system or workflow changed
- project/code context was discovered
- Sir Leo business, brand, offer, or pricing context changed
- a source was processed
- an output was created
- Leo says "remember this"
- the conversation would reduce future rediscovery

Skip memory check when:

- it was quick Q&A
- it was casual chat
- no decision, task, output, source, or durable preference emerged
- the idea was low confidence or throwaway
- Leo does not want it formalized

## Vault Handoff Format

Use this format when a memory check finds something worth preserving:

```markdown
# Vault Handoff

## Verdict

Save / Do not save

## Why

Short reason.

## Suggested Destination

raw/inbox, wiki, work, code, exports, or none.

## Items To Preserve

- Decisions:
- Preferences:
- Useful findings:
- Project/code context:
- Sources:
- Outputs:
- Open questions:

## Possible Tasks

- Task:
  - Outcome:
  - Definition of done:
  - Review required:

## Notes For Vault Maintainer

- Routing notes:
- Sensitivity/public-private concerns:
- Staleness or confidence notes:
```

## External Agent Instruction

Use this when an agent is not supposed to edit the vault, but may use the vault for relevant context:

```text
You do not need to edit my Leo Life Wiki vault. Do the requested work.

You may search/read the vault as context if it would help. Start with index.md or the specific page I point you to. Prefer reviewed/current pages, treat UNREVIEWED material as provisional, and do not modify vault files.

At the end, run a brief memory check. Only include a Vault Handoff if something from this conversation/work should be remembered, turned into a task, linked to a project, or preserved as an output. If nothing is worth saving, say: "Memory check: nothing worth saving."
```

## Vault Worker Instruction

Use this when an agent is supposed to edit the vault:

```text
You are working in my Leo Life Wiki vault.

First read:
1. AGENTS.md
2. wiki/07-systems/vault-maintainer-protocol.md

Then use wiki/07-systems/current-ai-takeover-handoff.md as a selective router
when needed. If I ask you to pick up queued work, follow
wiki/07-systems/queue-worker-bootstrap.md. Load only the relevant policy links,
make focused changes, update index.md and log.md only for meaningful changes,
and create attributed checkpoint commits for coherent slices.
```

For a fresh agent dedicated to processing `raw/inbox/`, use [[prompts-inbox-ingest-agent]].

For a fresh capable agent taking over general Leo Life Wiki work, use [[current-ai-takeover-handoff]].

## Linked Nodes

- implements: [[vault-operating-model]]
- related_to: [[vault-maintainer-protocol]]
- related_to: [[search-only-context-protocol]]
- related_to: [[external-work-protocol]]
- related_to: [[ask-leo-protocol]]
- related_to: [[inbox-routing-workflow]]
- related_to: [[prompts-inbox-ingest-agent]]
- related_to: [[current-ai-takeover-handoff]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[task-system]]
- related_to: [[codebase-memory-workflow]]
- related_to: [[agent-role-registry]]
- related_to: [[../../AGENTS]]
