---
title: Test Discovery Convention
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: technical/internal
tags:
  - systems
  - testing
  - ai-agents
  - verification
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Test Discovery Convention

## Purpose

Make verification easy for the next agent to discover. Tests should not merely
exist in a directory; the relevant workflow page and task packet should say how
to run them.

## Rule

When adding or changing a deterministic helper:

```text
add or update focused tests
-> document the narrow command near the workflow
-> include the command in the task packet when relevant
-> run the narrow command first
-> run the aggregate operational suite before committing shared behavior
-> record representative verification in task Activity
```

## Aggregate Operational Suite

```bash
python3 -m unittest discover -s scripts/tests -v
```

Run repository-specific suites as well when the selected task touches code
outside the vault scripts.

## Workflow Page Format

Each operational helper playbook should include:

```markdown
## Verify

```bash
python3 -m unittest scripts.tests.test_example -v
```

Before committing shared helper behavior:

```bash
python3 -m unittest discover -s scripts/tests -v
```
```

## Task Packet Rule

Use optional frontmatter when the command is stable and useful:

```yaml
verification_commands:
  - python3 -m unittest scripts.tests.test_example -v
```

For browser, integration, or external-service work, include the required manual
path in the Definition of Done as well.

## Linked Nodes

- implements: [[agent-completion-proof-protocol]]
- related_to: [[task-system]]
- related_to: [[queue-worker-bootstrap]]
