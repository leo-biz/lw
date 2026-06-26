---
title: Task System
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - playbook
  - tasks
  - ai-agents
  - ai-reviewed
created: 2026-05-29
updated: 2026-06-02
---

# Task System

## Purpose

Turn wiki knowledge, ingests, and decisions into trackable work. Tasks live in `work/` and move through folders by status.

## Folder = Status

```text
inbox/       INBOX       — captured, not triaged
ready/       READY       — triaged, actionable, unstarted
in-progress/ IN_PROGRESS — claimed and active
review/      REVIEW      — done, awaiting Leo review
blocked/     BLOCKED     — waiting on external dependency
done/        DONE        — complete and accepted
someday/     SOMEDAY     — parked, not actionable now
```

## Task Frontmatter

```yaml
id: task-YYYY-MM-DD-slug
title: ""
status: INBOX
domain: ""          # sir-leo | tech-career | business | learning | health | systems | personal
priority: P2        # P1 urgent | P2 normal | P3 low
quadrant: Q2        # Q1 urgent/important | Q2 important | Q3 urgent | Q4 neither
importance_reason: ""
urgency_reason: ""
human_effort: ""
ai_effort: ""
execution_mode: ""   # ai_only | ai_with_review | human_with_ai | human_only
human_input: ""
due: ""
agent: unassigned   # Claude | Leo | Jarvis | unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: ""          # wikilink to raw/ or wiki/ source that generated this task
wiki_page: ""       # wikilink to relevant wiki page
repo: ""            # project slug if code work (matches code/_registry)
export: ""          # target export path if task produces an output
leo_review_required: false
blocked_by: ""      # task id or external dependency description
depends_on: []      # directional dependency history; retain resolved task IDs
blocking: []        # active inverse of blocked_by; remove resolved task IDs
dependents: []      # durable inverse of depends_on; retain resolved task IDs
parent_task: ""
related_tasks: []
workstream: ""
handoff_checkpoint: ""
tags: []
```

Optional fields for multi-agent coordination and dashboard views:

```yaml
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
supersedes:
context_tags: []
heartbeat_eligible: false
autonomy: manual
worker_role:
capability_requirements: []
model_tier:
preferred_cost_tier:
required_tools: []
verification_commands: []
```

Keep common planning keys present even when empty so Obsidian Properties, Bases, scripts, and human scanning have a predictable shape. Omit transient lease fields and uncommon context-specific fields until they are useful.

Activity authors should be traceable to their worker thread. Use
`[agent:model](session-deep-link)` as the Activity author label whenever a
provider session is available. For Codex Desktop, the verified deep-link shape
is `codex://threads/<session_id>`, where `<session_id>` is `$CODEX_THREAD_ID`.
Preserve the plain `session_id` in lease frontmatter while the task is claimed.
When a provider has no verified link, use the best stable author label and
include the real session ID in the Activity text instead of inventing a URL.

Use `heartbeat_eligible`, `autonomy`, and `worker_role` only when unattended AI
selection is intentionally allowed. Follow [[autonomous-agent-heartbeats]].
Never infer unattended eligibility from `execution_mode`.

Use `worker_role`, `capability_requirements`, `model_tier`,
`preferred_cost_tier`, and `required_tools` only when routing materially
benefits. Follow [[worker-capability-routing]]. Use `verification_commands` when
a stable focused test command will help the next worker prove completion.

Use `depends_on` for durable directional task dependency history. Use
`blocked_by` for the currently unresolved hard-dependency subset that prevents
execution. On the prerequisite task, use `dependents` for durable downstream
history and `blocking` for the currently unresolved dependent subset. When a
dependency resolves, remove the relationship from `blocked_by` and `blocking`
but retain it in `depends_on` and `dependents`. Use `related_tasks` only for
explicit adjacent work without dependency direction, `parent_task` for an
umbrella program, `supersedes` for replacement history, and
`handoff_checkpoint` for the latest durable continuation point. Keep generated
similarity suggestions report-only until reviewed.

Use `related_tasks` as a small curated navigation set, not as a second notes
section. Add a relationship when two tasks should be discovered together
because they share a workstream, incident, design boundary, or follow-up
context, but neither task requires the other. Mirror the relationship on both
tasks when practical so navigation works in either direction. Keep the reason,
decision, implementation detail, and Activity in the task or wiki page that
owns that knowledge; do not copy the same notes into every related task.

Do not use `related_tasks` when a typed relationship is more accurate:

```text
requires another task       -> blocked_by + depends_on
required by another task    -> blocking + dependents
umbrella program            -> parent_task
replacement history         -> supersedes
adjacent, useful to discover -> related_tasks
```

Mirror directional dependency history in `## Linked Nodes`:

```markdown
- depends_on: `../done/example-dependency.md`
- dependents: `../ready/example-dependent.md`
```

Example while Task A requires Task B:

```yaml
# Task A
blocked_by: [task-b]
depends_on: [task-b]

# Task B
blocking: [task-a]
dependents: [task-a]
```

Use `sprint_id`, `sprint_start`, and `sprint_end` for a bounded planning window.
Named sprint windows live in `work/sprints.yaml`; task files remain the source
of truth for task assignment. Set `completed_at` when a task moves to `DONE` so
dashboards can show recent delivery without inferring it from file modification
time.

## Validate

Run the report-only lifecycle validator during end-of-work checks:

```bash
python3 scripts/task_lifecycle_validator.py
```

Repair or queue bounded legacy findings. Do not silently accept folder/status,
lease, checklist, or reciprocal dependency drift.

## Importance And Urgency

Classify importance and urgency separately when creating a task:

| Important? | Urgent? | Quadrant |
|---|---|---|
| yes | yes | `Q1` |
| yes | no | `Q2` |
| no | yes | `Q3` |
| no | no | `Q4` |

Urgency requires evidence: a deadline, active failure, blocked work, expiring opportunity, or waiting person. Do not treat recency, novelty, or interest as urgency.

Use `priority` to rank tasks within a quadrant:

```text
P1 select before similar tasks
P2 normal order
P3 defer unless capacity is available
```

Default to `quadrant: Q2` and `priority: P2` when evidence is incomplete. Add `importance_reason` and `urgency_reason` when the classification affects selection order.

## Effort And Human Input

Estimate human and AI effort separately. A task can be easy for an AI worker but still require a meaningful decision, approval, or source material from Leo.

Use `execution_mode` to answer whether AI can complete the task:

```yaml
human_effort: XS
ai_effort: M
execution_mode: ai_with_review
human_input: "Approve the proposed workflow after the sample run."
```

| Mode | Meaning |
|---|---|
| `ai_only` | AI can complete the task autonomously. |
| `ai_with_review` | AI can execute the task; Leo reviews or approves. |
| `human_with_ai` | Leo must take action; AI can assist. |
| `human_only` | Leo must complete the task without meaningful AI execution. |

Use coarse effort bands:

| Band | Meaning |
|---|---|
| `XS` | trivial or a few minutes |
| `S` | small bounded effort |
| `M` | normal focused work session |
| `L` | substantial multi-step work |
| `XL` | split into smaller tasks before execution |

Use `human_input` only when a specific human action is needed. Do not use effort
as a substitute for execution mode, importance, urgency, blockers, or approval
boundaries.

For `human_with_ai` and `human_only` tasks, make the human handoff as close to
mechanical as possible. Include:

```text
recommended name or option
exact destination URL or screen
ready-to-paste configuration when possible
small ordered checklist
where to store secrets or outputs
what not to paste into the vault or chat
the exact completion message to send back
```

Do not leave avoidable research, naming, formatting, or configuration assembly
for Leo when an agent can prepare it safely.

## Lease Semantics

A task lease is active while `lease_until` is in the future. Prefer the provider's stable thread or conversation ID for `session_id`; Codex Desktop exposes this as `$CODEX_THREAD_ID`. Add `session_provider` and a verified `session_url` when useful. Default to a two-hour lease unless the task calls for a shorter or longer window.

Use `scripts/task_lease.py` for local claim, renew, release, and expired-lease reclaim updates. It applies a short-lived local lock so two workers cannot mutate task leases simultaneously.

## How Agents Claim Tasks

1. Confirm that another worker does not hold an active lease.
2. Read recent activity before reclaiming an expired lease.
3. Run `python3 scripts/task_lease.py claim <ready-task> --agent <name> --session-id <unique-id>`.
4. Renew during longer work or release the lease when stopping without completion.
5. Append compact activity entries for meaningful progress beyond lease transitions.
6. Do not claim tasks marked `leo_review_required: true` unless Leo has assigned them.

Use `renew`, `release`, or `reclaim` in place of `claim` for those transitions. Only the owning `session_id` may renew or release. Reclaim is allowed only after `lease_until` has passed.

Fresh workers and dispatchers should use the deterministic picker. It
reconciles dependencies before ranking, excludes blocked and Leo-review-gated
tasks from its default shortlist, prints a compact selected-task packet, and
claims through `scripts/task_lease.py`:

```bash
python3 scripts/pick_next_task.py list --agent codex
python3 scripts/pick_next_task.py claim --agent codex --session-id "$CODEX_THREAD_ID"
python3 scripts/pick_next_task.py claim --task task-YYYY-MM-DD-slug \
  --agent codex --session-id "$CODEX_THREAD_ID"
```

Target quick-start flow for a fresh worker:

```text
reconcile dependencies
-> rank unblocked READY tasks
-> show the top candidates and reasons
-> atomically claim the selected task
-> include blockers, dependency deltas, related tasks, recent activity, and required policy links in the work packet
-> include capability requirements and verification commands when present
```

For the full cross-provider startup route, follow [[queue-worker-bootstrap]].
Do not load general recent work by default. Inspect dependency or related-task
updates only when they can change the selected task's assumptions.

Do not claim tasks marked `leo_review_required: true` without Leo assignment. Ranking should protect important `Q2` work from being displaced indefinitely by low-value `Q3` urgency.
Use effort to break ties, identify quick wins, and avoid assigning `XL` work without decomposition. Do not let low effort automatically outrank important work.

## Activity

Add an append-only activity section for meaningful state changes:

```markdown
## Activity

- 2026-05-30 14:00 | [codex:gpt-5](codex://threads/<session_id>) | Claimed task.
- 2026-05-30 14:18 | [codex:gpt-5](codex://threads/<session_id>) | Verified failure-path behavior.
- 2026-05-30 14:31 | [codex:gpt-5](codex://threads/<session_id>) | Ready for Leo review.
```

Record meaningful discoveries, blockers, approvals, and completions. Do not
store noisy internal reasoning. Do not bulk-rewrite old Activity entries just to
match this standard; apply it to new comments and touched task closeouts.

## When Tasks Move to Review

Move to `review/` when:
- All items in Definition of Done are checked off.
- Any output, export, or linked page is updated.
- `status:` is updated to `REVIEW`.

Use [[agent-completion-proof-protocol]] for code, automations, dashboards, and
meaningful vault workflow changes. Record the checks that prove the Definition
of Done rather than relying on file changes alone.

Before moving to `REVIEW` or `DONE`, add `## Review Proof` with:

- `### DoD Evidence`: each checked Definition of Done item mapped to evidence.
- `### See It Work`: how Leo can inspect, rerun, open, or approve a live run.
- Residual risk and skipped checks stated plainly.

Do not mark DONE yourself if `leo_review_required: true`. Stop at REVIEW.

## When Tasks Are Done

- Leo confirms review → move to `done/`, set `status: DONE`.
- If `leo_review_required: false` and the agent is confident → move directly to `done/`.

## Linking

| Field | Links to |
|---|---|
| `source` | `raw/` file or `wiki/` page that originated the task |
| `wiki_page` | the wiki page most relevant to this task |
| `repo` | managed code repo slug in `code/_registry/managed-repos.md` |
| `export` | target path in `exports/` if task produces deliverable output |

Use Obsidian wikilinks in the frontmatter fields where possible.

Body-level links that encode lifecycle folders such as `../ready/`,
`../in-progress/`, or `../done/` may become stale when a linked task moves.
Treat these as link-health findings: report them with
`scripts/wiki_health_check.py` and repair affected references selectively.
Lease helpers should not auto-rewrite arbitrary Markdown bodies. Keep hard
dependency semantics in task metadata: remove resolved reciprocal
`blocked_by` / `blocking` edges while retaining reciprocal
`depends_on` / `dependents` history.

## Leo Review Required

Set `leo_review_required: true` for any task that:

- Creates or edits content in `exports/public/` or `exports/client-facing/`
- Changes pricing, offer copy, or brand rules
- Moves `private/internal` material across the audience boundary
- Publishes or sends anything externally
- Makes a non-reversible structural change to the vault

Agents must stop at REVIEW for these tasks and wait for explicit Leo approval.

## Creating Tasks

Create tasks only when there is a clear outcome and definition of done.
Do not create tasks for things Leo will never realistically do.
Prefer one focused task over a vague catch-all.
Classify importance and urgency separately. Challenge weak urgency claims. Avoid retaining `Q4` tasks unless there is a concrete reason.

## Linked Nodes

- implements: [[../../work/README]]
- related_to: [[wiki-operating-rules]]
- related_to: [[learning-to-application-loop]]
- related_to: [[multi-agent-coordination]]
- related_to: [[task-dashboard]]
- related_to: [[agent-completion-proof-protocol]]
- related_to: [[autonomous-agent-heartbeats]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[worker-capability-routing]]
- related_to: [[test-discovery-convention]]
- related_to: [[../../AGENTS]]
