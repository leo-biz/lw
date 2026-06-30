---
# Required fields
id: task-2026-01-15-add-retry-logic-to-queue-worker        # unique slug, date-prefixed
title: Add retry logic to queue worker                     # human-readable
status: READY                                              # READY | IN_PROGRESS | REVIEW | DONE | BLOCKED

# Classification
domain: systems           # systems | ops | content | research | ...
priority: P2              # P1 (critical) | P2 (important) | P3 (nice-to-have)
quadrant: Q2              # Q1 (urgent+important) | Q2 (not-urgent+important) | Q3 | Q4

# Effort estimates
human_effort: S           # XS | S | M | L | XL
ai_effort: M              # XS | S | M | L | XL

# Execution
execution_mode: ai_with_review   # ai_only | ai_with_review | human | human_with_ai
human_input: "Review retry backoff constants before merge."

# Assignment (filled by queue worker when claimed)
agent: unassigned
session_id: ''

# Approval gate — set to true if the project owner must sign off before DONE
leo_review_required: false

# Dependencies — list other task IDs that must be DONE before this one is READY
depends_on:
  - task-2026-01-10-build-queue-worker-base

# Downstream tasks blocked by this one (auto-managed by dependency_reconciliation.py)
blocking: []

# Workstream grouping (optional, used for reporting)
workstream: queue-infrastructure

# Tags for search / filtering
tags:
  - systems
  - reliability
  - queue

# Dates (ISO 8601)
created: 2026-01-15
updated: 2026-01-15
due: ''
---

# Add retry logic to queue worker

## What

When a task claim fails due to a transient error (network timeout, lock
contention), the queue worker should retry up to 3 times with exponential
backoff before giving up and logging a structured error.

## Why

Currently a single failure aborts the entire claim cycle. Retries will
improve reliability in environments with intermittent I/O issues without
requiring operator intervention.

## Acceptance Criteria

- [ ] Retry up to 3 times with 1s / 2s / 4s delays.
- [ ] Log each retry attempt at WARNING level with attempt number and error.
- [ ] After 3 failures, raise a structured exception (not a bare `except`).
- [ ] Unit test covers: succeed on first try, succeed on second try, fail all three.
- [ ] No change to the external queue API surface.

## Review Proof

### DoD Evidence

_(Fill in once complete — paste test output, link to commit, or paste the
relevant log lines showing retry behavior.)_

### See It Work

```bash
# Run with a deliberately broken path to trigger retries
python3 scripts/pick_next_task.py claim --task nonexistent-id --agent test --session-id test-001
# Expected: 3 retry attempts logged, then structured error
```

### Residual Risk

- Retry loop adds up to 7 seconds of latency on total failure. Acceptable for
  background worker; may need a fast-fail flag for interactive use.

## Activity

- 2026-01-15 09:00 | human | Task created. Retry logic identified as gap after prod incident.
