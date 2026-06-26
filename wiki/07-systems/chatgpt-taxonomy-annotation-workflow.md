---
title: ChatGPT Taxonomy Annotation Workflow
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - playbook
  - chatgpt-export
  - taxonomy
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-30
---

# ChatGPT Taxonomy Annotation Workflow

Use `scripts/annotate_chatgpt_taxonomy.py`. Do not inspect or rewrite the script
unless the documented interface fails.

The script is dry-run first. It normalizes provisional taxonomy metadata, adds
major and minor tags, renders a compact linked taxonomy code below each raw note
title, and preserves conversation bodies.

## One-File Review

Start with one representative page:

```bash
python3 scripts/annotate_chatgpt_taxonomy.py \
  --file raw/chatgpt-export/<page>.md \
  --skip-taxonomy-page
```

Apply only after Leo approves the sample:

```bash
python3 scripts/annotate_chatgpt_taxonomy.py \
  --file raw/chatgpt-export/<page>.md \
  --skip-taxonomy-page \
  --apply
```

Repeat `--file` to process a selected subset.

## Bulk Run

Dry run:

```bash
python3 scripts/annotate_chatgpt_taxonomy.py
```

Apply only after sample approval:

```bash
python3 scripts/annotate_chatgpt_taxonomy.py --apply
```

## Expected Result

Each raw conversation page should retain provisional metadata and render a short
linked code directly below its title:

```yaml
taxonomy_code: E16
taxonomy_position: 701
taxonomy_status: AI_INFERRED
taxonomy_source: title-only
taxonomy_confidence: provisional
tags:
  - taxonomy/E
  - taxonomy/E16
```

```markdown
# 2004 Honda Civic Hybrid Crunching Sound

[[wiki/09-content-library/chatgpt-conversation-taxonomy#E16 - Automotive, Transportation & Mechanical|E16]]
```

## Validation

After any apply:

1. Run the same command again without `--apply`.
2. Confirm it reports `0 files would change`.
3. Inspect Git diff counts.
4. Confirm source conversation bodies did not drift.
5. Stage only the intended taxonomy batch.

## Known Inventory

- HTML export conversations: `925`
- Generated Markdown pages: `924`
- Missing Markdown page: position `300`, `G23`, `New chat`, ID `6848241a-9a94-800e-907f-5076ae009369`

## Linked Nodes

- operates_on: [[../09-content-library/chatgpt-conversation-taxonomy]]
- implements: [[vault-maintainer-protocol]]
- related_to: [[wiki-operating-rules]]
