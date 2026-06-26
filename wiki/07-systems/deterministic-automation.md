---
title: Deterministic Automation
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: technical/internal
tags:
  - systems
  - automation
  - scripts
  - ai-reviewed
created: 2026-05-30
updated: 2026-06-02
---

# Deterministic Automation

## Purpose

Run predictable recurring work without spending AI tokens.

AI should handle ambiguity, synthesis, judgment, and execution that benefits from reasoning. Normal scripts should handle repetitive state transitions and inventory work.

## Three Execution Tiers

### Tier 1: Deterministic Jobs

Use scripts without an AI model:

- YouTube playlist polling
- transcript capture
- manifest regeneration
- file inventories
- duplicate checks
- broken-link scans
- tag linting
- Git status summaries
- scheduled backups

### Tier 2: AI Review Queues

Use AI only when judgment adds value:

- select transcripts worth synthesizing
- summarize a bounded batch
- suggest tasks
- identify contradictions
- route ambiguous inbox material
- produce report-only health checks

### Tier 3: AI Work Agents

Use capable models for scoped execution:

- research
- coding
- drafting
- archive ingestion
- wiki synthesis
- exports

## Scheduler Rule

A scheduler should invoke scripts directly. Wake an AI agent only when:

- a review batch reaches a threshold
- a failure requires interpretation
- a report is due
- Leo assigns a task
- a deterministic job produces an exception worth investigating

## Run Logs

Routine jobs should write compact local JSONL logs:

```text
runs/
  youtube-queue.jsonl
  lint.jsonl
  health-check.jsonl
```

Example:

```json
{"time":"2026-05-30T14:00:00-05:00","job":"youtube-queue","captured":3,"existing":1,"failed":0,"moved":4}
```

Keep noisy run logs local and Git-ignored. Commit a synthesized report only when it has durable value.

Install the weekly report-only wiki health delta job with:

```bash
sh scripts/install_wiki_health_check_launchd.sh
```

## First Scheduler

The first scheduled deterministic job should be:

```bash
python3 scripts/youtube_queue.py --limit 5
```

Run it periodically with `launchd`. Notify Leo only for meaningful summaries or repeated failures.

Install the local six-hour schedule with:

```bash
sh scripts/install_youtube_queue_launchd.sh
```

Override the interval during install with `INTERVAL_SECONDS=<seconds>`. The job keeps compact summaries in the Git-ignored local file `runs/youtube-queue.jsonl`.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[youtube-transcript-workflow]]
- related_to: [[autonomous-agent-heartbeats]]
- related_to: [[wiki-health-check]]
- related_to: [[multi-agent-coordination]]
- related_to: [[task-dashboard]]
- related_to: [[agent-system]]
