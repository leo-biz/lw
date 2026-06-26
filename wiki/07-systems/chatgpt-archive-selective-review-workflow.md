---
title: ChatGPT Archive Selective Review Workflow
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - chatgpt-export
  - archive-review
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-30
---

# ChatGPT Archive Selective Review Workflow

## Purpose

Review the preserved ChatGPT export in bounded batches and extract only durable knowledge, decisions, contradictions, and useful work.

The archive is evidence, not a backlog of pages that must each become wiki notes.

## Review Order

Prioritize batches tied to active operating areas:

1. Sir Leo brand, offers, and experiences (`C08`)
2. business, consulting, and operations (`B06`)
3. careers and professional development (`B05`)
4. AI, data analysis, and knowledge systems (`A21`)
5. identity, relationships, and personal areas when Leo approves the scope
6. lower-value reference clusters only when they support current work

Size batches by review load, not file count alone. Before selecting a batch, run:

```bash
python3 scripts/chatgpt_archive_inventory.py --cluster C08 --csv
```

Default batch budget:

```text
target: 80-150 messages
soft character cap: 150,000
conversation count: usually 5-12 files
```

Split conversations larger than the soft cap into dedicated review tasks. Adjust the budget only after a pilot shows the review quality and context cost are reasonable.

## Triage Packet Pipeline

Before bulk archive review, add a report-only packet generator:

```text
raw conversation
-> parse role-prefixed messages
-> annotate low-information messages
-> conservatively merge context-dependent short messages with neighbors
-> split oversized conversations on message boundaries
-> emit traceable chunk packets
-> compact chunk summaries
-> roll up one conversation summary
-> queue deep review only when durable value or uncertainty is present
```

Recommended chunk defaults:

```text
target chunk: 20,000-35,000 characters
maximum chunk: 50,000 characters
overlap: previous chunk summary plus the last 2-4 messages
```

Every packet must preserve:

```text
conversation ID
source path
chunk ID
original message range
message count
character count
merge annotations
```

Do not delete short messages solely because they are short. Merge greetings, filler, duplicate acknowledgements, and formatting-only messages conservatively. Preserve or attach numbers, prices, dates, names, URLs, corrections, approvals, rejections, negations, and short commands to neighboring context.

Keep raw Markdown unchanged. Store packet and triage output separately until the format proves trustworthy. Audit a random sample of dismissed packets before scaling.

### Packet Generator Operator Card

Use the deterministic generator before any AI archive review:

```bash
python3 scripts/chatgpt_archive_packets.py --cluster C08 --limit 5 --batch-id C08-sample --markdown
```

Default thresholds:

```text
target chunk: 30,000 characters
maximum chunk: 50,000 characters
overlap: previous chunk summary ref plus last 3 messages
```

Outputs are report-only and live outside raw sources:

```text
runs/chatgpt-archive-review/
  packets.jsonl
  packets-md/
  chunk-summaries.jsonl
  conversation-rollups.jsonl
  concept-hints.jsonl
  concept-clumps.jsonl
  concept-audit.jsonl
  dismissal-audit.jsonl
  checkpoints.jsonl
```

Failure behavior:

- The script exits non-zero when chunk thresholds are invalid.
- Raw `raw/chatgpt-export/` Markdown is read-only input and must not be modified.
- Existing chunk summaries, rollups, concept files, and checkpoints are append-friendly state files for continuation.
- `packets.jsonl` and `packets-md/` are regenerated packet views for the selected batch.
- `dismissal-audit.jsonl` lists low-information or tiny packet candidates that require Leo/sample review before any bulk dismissal.
- `concept-hints.jsonl`, `concept-clumps.jsonl`, and `concept-audit.jsonl` are provisional retrieval aids, not wiki truth.

Layered compaction contract:

```text
packet -> chunk summary -> final conversation rollup -> optional provisional concept hints/clumps
```

Each packet carries a `review_contract` requiring a chunk summary, requiring a conversation rollup on the final chunk, and forbidding raw-source mutation. Checkpoints record `last_completed_packet`, `next_packet`, completed and remaining packet IDs, open questions, Leo-review items, and proposed wiki updates so a fresh provider thread can continue without rereading completed chunks.

Concept operations are optional JSONL records applied with `--concept-ops`:

```json
{"operation":"rename","concept_id":"concept-sir-leo-brand","label":"Sir Leo identity"}
{"operation":"defer","concept_id":"concept-pricing-and-offers","reason":"Wait for Leo pricing review."}
{"operation":"merge","target_concept_id":"concept-sir-leo-brand","source_concept_ids":["concept-social-media-content"],"label":"Sir Leo brand and content"}
{"operation":"split","source_concept_id":"concept-events-and-experiences","new_concept_id":"event-invite-copy","label":"Event invite copy","packet_ids":["...-chunk-001"]}
```

All operation output remains `PROVISIONAL` and must not edit raw sources.

## Provisional Concept Clumps

Triage should preserve partial memory before deep review. A packet may reveal only that several conversations appear related to the same concept. Record that association without promoting it to settled wiki knowledge.

```text
packet hints
-> provisional concept labels
-> related-source clumps
-> confidence and evidence pointers
-> deep review when the concept becomes useful or sufficiently connected
```

Store provisional concept memory separately from raw sources and durable wiki synthesis:

```text
runs/chatgpt-archive-review/
  concept-hints.jsonl
  concept-clumps.jsonl
```

Concept hints should record:

```yaml
concept_id:
label:
source_packet:
source_message_ranges:
confidence:
reason:
related_concepts:
status: PROVISIONAL
```

Concept clumps should record:

```yaml
concept_id:
label:
source_packets:
related_concepts:
open_questions:
deep_review_trigger:
status: PROVISIONAL
```

Use these clumps as a retrieval map, not as authoritative synthesis. Promote a concept into `wiki/` only after deeper review establishes durable value, evidence, scope, and relationship to existing pages. Merge or split provisional concepts freely while they remain outside the wiki layer.

A provisional clump is ready to promote only when deeper review confirms:

- the clump points to durable knowledge, a decision, a reusable practice, or a real task
- evidence spans the cited packets and does not depend on title-only inference
- sensitive/private-boundary content is reviewed before public or client-facing use
- contradictions and stale claims are resolved or explicitly flagged
- Leo has approved promotion when brand, pricing, offers, private strategy, or personal material is involved

## Resumable Thread Handoffs

Treat provider threads as temporary workers. A fresh thread should be able to continue archive review without rereading completed raw chunks or replaying an old conversation.

Store resumable packet state outside raw sources:

```text
runs/chatgpt-archive-review/
  packets.jsonl
  chunk-summaries.jsonl
  conversation-rollups.jsonl
  concept-hints.jsonl
  concept-clumps.jsonl
  checkpoints.jsonl
```

Each checkpoint should record:

```yaml
time:
task_id:
session_id:
batch_id:
last_completed_packet:
next_packet:
completed_packets:
remaining_packets:
rollups_updated:
concept_clumps_updated:
open_questions:
leo_review_items:
wiki_updates_proposed:
```

When a thread approaches context limits or reaches a clean phase boundary:

1. finish the current packet instead of starting another
2. persist the chunk summary and any conversation rollup
3. append one compact checkpoint
4. update task activity with the last completed and next packet IDs
5. release or allow expiry of the task lease
6. hand the next thread the task, checkpoint, rollups, and next bounded packet only

Use [[prompts-chatgpt-archive-review-thread-handoff]] as the compact handoff template.

## Per-Conversation Outcomes

After reviewing one raw conversation, preserve its body and update only frontmatter:

```yaml
status: AI_REVIEWED
archive_review_outcome: extracted
archive_review_batch: C08-001
archive_reviewed_date: YYYY-MM-DD
```

Allowed outcomes:

```text
extracted          durable value was added to wiki, work, or a decision queue
no-durable-value   reviewed and intentionally dismissed
needs-leo-review   potentially useful, sensitive, contradictory, or unclear
```

Do not mark a source `HUMAN_REVIEWED` unless Leo explicitly approves it.

## Batch Workflow

1. Select a coherent cluster and list the exact source files, message count, and character count in one task.
2. Read only that bounded set.
3. Preserve raw conversation bodies.
4. Extract durable knowledge into focused existing wiki pages when possible.
5. Create new wiki pages only when the material deserves a durable retrieval point.
6. Create tasks only for clear outcomes with a definition of done.
7. Flag contradictions, stale claims, and sensitive decisions for Leo.
8. Update source frontmatter with one allowed review outcome.
9. Update [[../09-content-library/chatgpt-archive-review-dashboard|ChatGPT Archive Review Dashboard]].
10. Validate file counts, source-body preservation, and exact staging scope before committing.

## Review Standard

A useful batch report should answer:

- Which conversations were reviewed?
- Which were dismissed with no durable value?
- Which wiki pages or tasks changed?
- Which claims need Leo review?
- What should the next batch cover?

Do not bulk-review the archive merely to reduce a count. The goal is reusable understanding, not mechanical completion.

## Linked Nodes

- operates_on: [[../09-content-library/chatgpt-conversation-taxonomy]]
- tracks_with: [[../09-content-library/chatgpt-archive-review-dashboard]]
- related_to: [[chatgpt-taxonomy-annotation-workflow]]
- related_to: [[prompts-chatgpt-archive-review-thread-handoff]]
- implements: [[vault-maintainer-protocol]]
