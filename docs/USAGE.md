# Usage Guide — leo-agent-tooling

## Requirements

- Python 3.10+
- No external dependencies for core task queue scripts
- `PyYAML` for scripts that parse frontmatter (install with `pip install pyyaml`)

## Setup

```bash
# Clone the repo
git clone https://github.com/<your-org>/leo-agent-tooling.git
cd leo-agent-tooling

# Optional: create a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies (if any are added)
pip install -r requirements.txt  # not required for core scripts
```

## Core Scripts

### pick_next_task.py — claim the next eligible task

```bash
# Claim the next task from the queue
python3 scripts/pick_next_task.py claim --agent <agent-name> --session-id <session-id>

# Claim a specific task by ID
python3 scripts/pick_next_task.py claim --task <task-id> --agent <agent-name> --session-id <session-id>
```

Tasks are Markdown files with YAML frontmatter. The script scans `work/ready/`
for tasks whose dependencies are met and leases the best match.

### task_lease.py — manage task leases

```bash
# Complete a task
python3 scripts/task_lease.py complete <path/to/task.md> --agent <agent-name> --session-id <session-id>

# Submit a task for review
python3 scripts/task_lease.py submit <path/to/task.md> --agent <agent-name> --session-id <session-id>
```

### task_relationship_report.py — dependency graph report

```bash
python3 scripts/task_relationship_report.py
```

Prints a summary of task dependencies, blocked tasks, and workstream groupings.

### dependency_reconciliation.py — fix stale blocked_by state

```bash
python3 scripts/dependency_reconciliation.py
```

Scans all tasks, resolves completed dependencies, and updates `blocked_by` lists.

### context_packet_builder.py — build agent handoff context

```bash
python3 scripts/context_packet_builder.py --task <task-id>
```

Assembles a focused context packet (task card + related wiki pages + recent
activity) for passing to an LLM agent at handoff.

### publication_scanner.py — pre-publish safety scanner

```bash
# Scan a directory before pushing to GitHub
python3 scripts/publication_scanner.py exports/github-preview/ --strict

# Use a custom allowlist for known false positives
python3 scripts/publication_scanner.py <dir> --strict --allowlist scripts/scanner_allowlist.txt
```

Detects secrets, private audience markers, local home paths, and other
publication boundary violations.

## Task File Format

Tasks are Markdown files stored in `work/` subdirectories (`ready/`,
`in-progress/`, `review/`, `done/`). Each file starts with YAML frontmatter:

```yaml
---
id: task-YYYY-MM-DD-short-slug
title: Human-readable title
status: READY
domain: systems
priority: P1
quadrant: Q1
agent: unassigned
leo_review_required: false
depends_on: []
blocking: []
---
```

See `examples/example-task.md` for a complete annotated example.

## Running Tests

```bash
python3 -m pytest scripts/tests/ -v
```

Or run individual test files:

```bash
python3 -m pytest scripts/tests/test_task_lease.py -v
python3 -m pytest scripts/tests/test_publication_scanner.py -v
```

## Directory Layout

```
.
├── README.md
├── LICENSE
├── docs/
│   └── USAGE.md          # this file
├── examples/
│   └── example-task.md   # annotated example task card
├── scripts/
│   ├── pick_next_task.py
│   ├── task_lease.py
│   ├── task_relationship_report.py
│   ├── dependency_reconciliation.py
│   ├── context_packet_builder.py
│   ├── publication_scanner.py
│   ├── scanner_allowlist.txt
│   └── tests/
│       ├── test_task_lease.py
│       ├── test_task_relationship_report.py
│       └── test_publication_scanner.py
└── .gitignore
```
