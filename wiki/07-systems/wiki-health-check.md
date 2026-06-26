---
title: Wiki Health Check
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: technical/internal
tags:
  - systems
  - automation
  - health-check
  - ai-reviewed
created: 2026-05-30
updated: 2026-06-02
---

# Wiki Health Check

## Purpose

Surface vault maintenance issues without automatically rewriting wiki pages.

Run the deterministic scan manually before scheduling it:

```bash
python3 scripts/wiki_health_check.py \
  --output .tmp/wiki-health-check.md \
  --log-jsonl runs/health-check.jsonl
```

The Markdown report is disposable unless a specific result has durable value. Compact JSONL summaries stay local and Git-ignored.

## Deterministic Checks

- broken Obsidian wikilinks
- malformed YAML frontmatter
- wiki pages older than the configured stale threshold
- wiki pages missing `updated`
- wiki pages without incoming Obsidian wikilinks
- wiki pages missing a provenance link
- missing, malformed, duplicate, or non-normalized tags
- files waiting in `raw/inbox/`
- raw Markdown files marked `UNREVIEWED`

Link lint excludes `raw/` source bodies because preserved transcripts and exports may contain bracket-like source text that is not Obsidian navigation. Raw processing state is still inventoried separately.

Defaults:

```text
stale threshold: 90 days
report list limit: 20 items per section
```

Override them with `--stale-days` and `--max-items`.

## AI Judgment Queue

Actual contradictions require semantic review. The deterministic report identifies a bounded starting queue:

- stale pages with `current` in the title
- pages marked `NEEDS_REVISION`
- a reminder to compare current decisions and claims manually

Do not allow scheduled agents to rewrite wiki pages until report quality is trusted and Leo explicitly approves an edit workflow.

## Weekly Delta Job
Run `python3 scripts/scheduled_wiki_health_check.py` manually or install the
weekly job with `sh scripts/install_wiki_health_check_launchd.sh`. It appends
`runs/health-check.jsonl`, writes `.tmp/wiki-health-check.md`, and creates at
most one READY review task for actionable deltas. Failures go to
`runs/wiki-health-check.stderr.log`; no content edits run automatically.

## Linked Nodes

- implements: [[deterministic-automation]]
- related_to: [[wiki-operating-rules]]
- related_to: [[vault-maintainer-protocol]]
