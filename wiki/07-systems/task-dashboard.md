---
title: Task Dashboard
node_type: hypothesis
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - tasks
  - dashboard
  - kanban
  - ai-reviewed
created: 2026-05-30
updated: 2026-06-02
---

# Task Dashboard

## Purpose

Provide a better operational view over Markdown tasks without creating a competing task database.

```text
Markdown task files = source of truth
local dashboard = operational view
Slack = conversation and approvals
```

## MVP

Build a local dashboard that reads `work/**/*.md` frontmatter and renders:

```text
Inbox | Ready | In Progress | Review | Blocked | Done | Someday
```

Each card should show:

```text
title
owner
priority
quadrant
domain
due date
lease expiry
last activity
review required
human effort
AI effort
human input
```

Clicking a task should reveal:

```text
definition of done
source links
wiki links
activity history
comments
blockers
outputs
```

## Local Markdown-Backed Dashboard

The dashboard is implemented with `scripts/task_dashboard.py` and static files under `dashboard/`.

```bash
python3 scripts/task_dashboard.py
```

Open `http://127.0.0.1:8765`. The dashboard reads Markdown task files and
Git-ignored `runs/*.jsonl` automation summaries on each API refresh. Dragging a
Kanban card moves the Markdown file and updates its frontmatter atomically. The
detail panel can assign a task to a named sprint window, and Definition of Done
checkboxes update the existing Markdown checklist. The dashboard does not
create a second task database.

When a human-action task provides `Recommended App Name`, `Remaining Setup
Reminder`, or `App Manifest Reference` sections, render those sections in the
task drawer so Leo does not need to open the Markdown source to find the
handoff packet.

The local write surface stays intentionally narrow:

```text
status move
sprint assignment
named sprint-window creation
definition-of-done checkbox update
completion timestamp
append-only activity entry
```

Do not override active agent leases from the dashboard. Use
`scripts/task_lease.py` for worker lease transitions.

Dashboard moves to `REVIEW` or `DONE` reject unchecked Definition of Done items.
Verify lifecycle state with:

```bash
python3 scripts/task_lifecycle_validator.py
```

## Native Obsidian Base

`work/tasks.base` provides a native Obsidian operational view over the same Markdown task properties:

```text
Active
Ready
In Progress
Blocked
Waiting On Leo
Leo Tasks
Sprint Planning
Recently Completed
Archive Review
Recently Active
```

Use the Base for quick property inspection and lightweight edits inside Obsidian. Use the local dashboard when Kanban cards, task details, and automation summaries are more useful. Both remain views over Markdown files.

## Useful Views

- Kanban
- Today
- My Tasks
- Sprints
- Waiting On Me
- Agent Activity
- Goals
- Automation Runs

## Task Metadata

Add optional fields only when useful:

```yaml
quadrant: Q2
due:
agent: unassigned
claimed_at:
lease_until:
session_id:
session_provider:
session_url:
goal:
project:
last_activity:
sprint_start:
sprint_end:
sprint_id:
completed_at:
parent_task:
depends_on: []
blocking: []
dependents: []
related_tasks: []
supersedes:
workstream:
context_tags: []
handoff_checkpoint:
human_effort:
ai_effort:
execution_mode:
human_input:
```

Omit empty optional keys when context efficiency matters.

Render `session_url` as a click-through link only when it is verified. Otherwise show the real `session_id` as copyable text. For Codex Desktop, use `$CODEX_THREAD_ID` and the verified thread route `codex://threads/<session_id>`.

## Quadrants

Use Stephen Covey's compact importance/urgency notation:

```text
Q1 = important and urgent
Q2 = important and not urgent
Q3 = not important and urgent
Q4 = not important and not urgent
```

Keep `priority: P1 | P2 | P3` for ordering tasks inside a quadrant.

## Build Order

1. Extend Markdown task conventions with claims, leases, activity, and quadrants.
2. Build a read-only Kanban view.
3. Add Markdown-backed editing.
4. Add Slack task links and approvals.
5. Add automation-run summaries.
6. Add goal views after the basic workflow proves useful.
7. Add live Agent Activity from [[agent-presence-ledger]] after the local helper proves useful.

## Activity

- 2026-05-31 07:21 | codex | Added Markdown-backed status moves, shared task-write locking, Leo-focused task visibility, sprint planning windows, recent completion visibility, explicit mobile-friendly move controls, and completion-date backfill for existing done tasks.
- 2026-05-31 07:35 | codex | Added named custom-date sprint creation, previous-sprint navigation and metrics, task-to-sprint assignment, and writable Definition of Done checkboxes backed by the existing Markdown checklist.
- 2026-05-31 07:55 | codex | Rendered human-action handoff sections directly in the dashboard task drawer and made the Slack secret-storage checklist item name the exact env-file path.

## Linked Nodes

- implements: [[task-system]]
- related_to: [[multi-agent-coordination]]
- related_to: [[slack-agent-command-center]]
- related_to: [[deterministic-automation]]
- related_to: [[agent-presence-ledger]]
