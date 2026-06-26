---
title: Old Conversation Memory Check Prompt
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - memory-check
  - prompt
  - ai-reviewed
created: 2026-05-29
updated: 2026-05-29
---

# Old Conversation Memory Check Prompt

## Purpose

Use this prompt to process old conversations without dumping everything into the vault.

The goal is not to summarize the entire conversation. The goal is to extract durable items worth preserving.

## Prompt

```text
Run a memory check on this old conversation.

Do not summarize everything.

Extract only durable items worth preserving in Leo Life Wiki:
- decisions
- durable preferences
- active or implied tasks
- project/code context
- reusable workflows
- useful outputs
- source material worth preserving
- open questions worth tracking
- contradictions or stale ideas to flag

Ignore:
- filler
- repeated context
- casual chatter
- low-confidence ideas
- abandoned ideas unless historically useful
- outdated versions unless they should be marked old, experimental, archived, or superseded

Produce a Vault Handoff using this format:

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
- Superseded or stale items:

## Possible Tasks

- Task:
  - Outcome:
  - Definition of done:
  - Review required:

## Notes For Vault Maintainer

- Suggested routing:
- Sensitivity/public-private concerns:
- Confidence notes:
- What not to save:

If nothing is worth preserving, respond only:

Memory check: nothing worth saving.
```

## Batch Guidance

Process old conversations by theme when possible:

- Sir Leo
- AI/wiki system
- code/projects
- business ideas
- fitness
- tech career
- learning

Prioritize recent or high-value conversations before older archives.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[inbox-routing-workflow]]
- related_to: [[vault-operating-model]]
