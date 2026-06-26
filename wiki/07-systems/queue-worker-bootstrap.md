---
title: Queue Worker Bootstrap
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - tasks
  - context-engineering
  - ai-reviewed
created: 2026-05-31
updated: 2026-06-07
---

# Queue Worker Bootstrap

## Purpose

Let a fresh agent from any provider pick up useful queued work with a small
prompt and consistently discover the standards relevant to that task.

This is a routing protocol. It should lead the worker down the right rabbit
holes without loading the whole vault.

## Startup

After Leo confirms Vault Worker mode:

```text
read this page
-> inspect dirty ownership
-> register local agent presence
-> list compact eligible task IDs through the deterministic picker
-> return to Leo for selection unless Leo or a dispatcher already assigned a task
```

Do not open READY task cards before selection. The report-only shortlist is the
pre-selection context boundary.

## After Selection

```text
claim the selected eligible task
-> read the claimed Markdown task card once (DoD, Activity, relationships are there)
-> follow only the policy links required by its surface area
-> execute one bounded coherent slice
-> validate, checkpoint-commit with attribution, and release file claims
-> complete, submit, or release the task lease
-> run budget preflight before claiming related work
```

Use the deterministic picker to reconcile dependencies, rank eligible tasks,
show a compact shortlist, inspect recently created tasks, and claim the selected
task:

```bash
# Ranked eligible work, not a recency view.
python3 scripts/pick_next_task.py list --agent codex

# Recently created tasks in the READY column. Use this when Leo asks for
# recent READY tasks, newest tasks, or queue order by date.
python3 scripts/pick_next_task.py list --agent codex --recent

python3 scripts/pick_next_task.py claim --agent codex --session-id "$SID"
python3 scripts/pick_next_task.py claim --task task-YYYY-MM-DD-slug \
  --agent codex --session-id "$SID"
```

Report-only listing excludes blocked and Leo-review-gated tasks by default.
Explicit selection is the assignment path when Leo or a dispatcher chooses a
review-gated task.

Do not substitute `ls work/ready`, filename sorting, or the default eligible
shortlist for a recent-by-date queue view. `--recent` is the canonical
pre-selection view for recently created tasks and stays inside the no-task-body
context boundary.

Before any script calls, bind the session ID once from the runtime env:

```bash
SID="${CLAUDE_CODE_SESSION_ID:-${CODEX_THREAD_ID:-}}"
# Reuse SID in every script call. sqz also injects __SQZ_CMD when available.
```

Routine startup needs this command card; register presence before claiming
anything and claim intended paths before editing:

```bash
python3 scripts/agent_presence.py start \
  --agent codex --provider openai --session-id "$SID" --role coder \
  --current-slice "Scanning ready queue"
python3 scripts/file_claims.py status
python3 scripts/file_claims.py claim path/to/intended-file \
  --agent codex --provider openai --session-id "$SID" \
  --task-id task-YYYY-MM-DD-slug
```

`task_lease.py` warns at claim time when presence registration was skipped.
Update `--current-slice` at each meaningful phase. Mark the session ended before
leaving:

```bash
python3 scripts/agent_presence.py end \
  --session-id "$SID" \
  --last-commit "$(git rev-parse --short HEAD)" \
  --handoff-checkpoint "Brief next-step note here."
```

Load [[agent-presence-ledger]] or [[file-claim-ledger]] only for exceptions:
overlapping claims, takeover, reclaim, expired state, or troubleshooting.

## Closeout

When the assigned outcome is finished, check `leo_review_required` on the task
and use the right closing verb:

| `leo_review_required` | Verb | Destination | Status |
|---|---|---|---|
| `false` | `complete` | `work/done/` | `DONE` |
| `true` | `submit` | `work/review/` | `REVIEW` |

```bash
# Task is done, no Leo sign-off needed
python3 scripts/task_lease.py complete work/in-progress/my-task.md --agent codex --session-id "$SID"

# Task needs Leo to review before closing
python3 scripts/task_lease.py submit work/in-progress/my-task.md --agent codex --session-id "$SID"

# Both also accept bare task IDs
python3 scripts/task_lease.py complete task-2026-05-31-my-task --agent codex --session-id "$SID"
```

`release` returns the task to `work/ready/` — it is only for yielding
unfinished work back to the queue, not for closing it out. `complete` will
error if called on a `leo_review_required: true` task and will tell you to use
`submit` instead.

## Always Load

Keep the mandatory core small:

1. `AGENTS.md`
2. this page
3. the confirmed mode protocol
4. the selected Markdown task

Load [[agent-completion-proof-protocol]] before declaring substantive work
complete.

The embedded commands cover routine operation; load a full policy only when the
selected task crosses its surface or an exception needs detail.

## Compact Task Packet

For the selected task, gather only:

```text
task metadata and Definition of Done
checkpoint and recent Activity
hard dependencies, durable depends_on/dependents history, and tasks directly blocked by this task
explicit related_tasks and same-workstream context when useful
linked wiki_page, source, repo, and export when populated
approval boundary
required policy links from the matrix below
worker capability requirements and minimum model tier when present
verification commands when present
```

If a dependency or related task recently changed the assumptions for the
selected work, inspect that task's latest checkpoint, Activity, and relevant
commits or diffs. Do not load general recent history by default.

Use the packet builder when launching a fresh worker session, handing context to
Slack preview/chat surfaces, comparing answers across agents, or recovering
after context clearing:

```bash
python3 scripts/context_packet_builder.py task-YYYY-MM-DD-slug
python3 scripts/context_packet_builder.py work/in-progress/my-task.md --type read-only-chat
python3 scripts/context_packet_builder.py task-YYYY-MM-DD-slug --type review --json
python3 scripts/context_packet_builder.py task-YYYY-MM-DD-slug --type ask-many --prompt "Compare approaches."
```

Audience gates fail closed. `private/internal` is the default and can include
vault-local task facts. `public` and `client-facing` packets are only generated
when the task frontmatter explicitly declares the matching `audience`; otherwise
the builder returns `PACKET_BLOCKED_BY_AUDIENCE` without the task body.

Same-session continuation does not need a rebuilt packet when the current agent
still has fresh task context, owns the lease, and no linked dependency changed.
Rebuild the packet when a new provider/session/Slack surface is involved, the
agent cleared context, a dependency or related task moved, or the audience
boundary changes.

## Policy Router

Load a policy only when the task crosses that surface:

| Surface | Required Entry Point |
|---|---|
| Vault edits | [[vault-maintainer-protocol]] |
| Claim overlap, dirty ownership, reclaim, or takeover | [[file-claim-ledger]] |
| Multi-agent coordination exception or relationship repair | [[multi-agent-coordination]] |
| Completion or review | [[agent-completion-proof-protocol]] |
| Raw source ingest | [[inbox-routing-workflow]] |
| YouTube transcript work | [[youtube-transcript-workflow]] |
| Learning synthesis | [[learning-to-application-loop]] |
| Opted-in codebase memory | [[codebase-memory-workflow]] |
| Public, team, client, or private export | [[vault-operating-model#Public vs Private Boundary]] |
| Scheduled deterministic work | [[deterministic-automation]] |
| Autonomous continuation preflight | [[autonomous-agent-heartbeats#Universal Budget Preflight]] |
| Provider-budget preflight checklist | [[provider-budget-preflight-operator-card]] |
| Provider continuation controls (goals, loops, automations) | [[continuation-operator-card]] |
| Slack dispatch | [[slack-agent-command-center]] |
| ChatGPT archive review | [[chatgpt-archive-selective-review-workflow]] |
| Worker or model selection | [[worker-capability-routing]] |
| Missing or unstable verification commands, or helper workflow changes | [[test-discovery-convention]] |

Follow directly linked domain pages when the task points to them. Do not infer
that every task needs every protocol.

## Context Tool Rule

Use `sqz` for repeated or large file reads, large diffs, command output, and
handoff inspection when the current platform exposes the capability. Load
[[sqz-context-compression]] for `expand`, `passthrough`, or troubleshooting.

Do not use lossy compression as the sole read path when exact wording, raw
evidence, pricing, public copy, secrets, or safety-critical details matter.
Perform a targeted direct read for those passages. If `sqz` is unavailable,
fall back to targeted reads and state that briefly rather than bulk-loading.

## Dependency-Aware Continuation

Before starting or continuing:

1. inspect hard dependencies
2. identify dependencies completed since the task was last touched
3. read only the changed assumptions, checkpoint, Activity, and relevant commit
4. prefer newly-unblocked or explicitly related follow-up work when the current
   context makes it cheaper
5. run [[autonomous-agent-heartbeats#Universal Budget Preflight]] before another
   substantial phase or related-task claim

## Small Cross-Provider Prompt

Leo-facing copy-paste card: [[prompts-queue-worker]]

```text
Read AGENTS.md and follow its mode-confirmation gate. After confirmation, follow
wiki/07-systems/queue-worker-bootstrap.md. Pick up the next eligible queued task,
claim it, load only its compact packet and required policy links, use sqz for
repeated or large reads when available, complete one bounded coherent slice,
validate it, checkpoint-commit with attribution, and continue into related work
only if budget preflight says it is safe.
```

## Linked Nodes

- implements: [[task-system]]
- related_to: [[current-ai-takeover-handoff]]
- related_to: [[multi-agent-coordination]]
- related_to: [[sqz-context-compression]]
- related_to: [[autonomous-agent-heartbeats]]
- related_to: [[prompts-queue-worker]]
- related_to: [[agent-presence-ledger]]
- related_to: [[worker-capability-routing]]
- related_to: [[test-discovery-convention]]
- related_to: [[continuation-operator-card]]
- related_to: [[provider-budget-preflight-operator-card]]
