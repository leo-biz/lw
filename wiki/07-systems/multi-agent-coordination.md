---
title: Multi-Agent Coordination
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - tasks
  - coordination
  - ai-reviewed
created: 2026-05-30
updated: 2026-05-30
---

# Multi-Agent Coordination

## Purpose

Let multiple AI providers, sessions, and scheduled workers cooperate without duplicating work or loading unnecessary context.

## Source Of Truth

```text
Slack = conversation, dispatch, approvals, alerts
vault = durable memory, tasks, decisions, outputs
Git = history
scripts = routine deterministic automation
agents = judgment and execution
```

Slack is useful as a human-facing command center. It must not become the only task database or durable memory layer.

Use [[agent-control-plane-operating-model]] for the vocabulary that separates
models, agents, sessions, context, memory, dispatchers, workers, adapters, and
orchestrators.

## Roles And Temporary Threads

Use a small reusable role registry and temporary provider threads. The vault should remember the work; provider chats should remain disposable execution contexts.

Agents should proactively recommend a fresh role-specific thread when a task is complete, a coherent phase ends, the role changes, or context becomes noisy:

```text
Good handoff point: start a fresh <role> thread for <task>.
```

See [[agent-role-registry]].

## Agent Presence

For substantial queue or vault work, register local lifecycle presence through
[[agent-presence-ledger]]:

```bash
python3 scripts/agent_presence.py start \
  --agent codex \
  --provider openai \
  --session-id "$CODEX_THREAD_ID" \
  --task-id task-YYYY-MM-DD-example \
  --current-slice "Implement bounded helper"

python3 scripts/agent_presence.py status
```

Record meaningful heartbeats during longer slices. Before leaving, mark the
session `end`, `stop`, `wait`, or `block`, include the latest commit or
handoff checkpoint when useful, and release file claims. Keep noisy operational
presence local; durable milestones still belong in task Activity and Git.

## Task Claims

Tasks should support optional lease fields:

```yaml
agent: unassigned
claimed_at:
lease_until:
session_id:
session_provider:
session_url:
last_activity:
```

Claim flow:

1. Agent reads the task and checks recent activity.
2. Agent confirms that no active lease belongs to another worker.
3. Agent claims the task with `scripts/task_lease.py`; the helper sets owner, claim time, lease expiry, and session ID and moves the task into `work/in-progress/`.
4. Agent renews the lease during longer work or releases it back to `READY` when stopping without completing the task.
5. An expired lease may be reclaimed only after checking activity history for evidence that another worker is still active.

A lease is active while `lease_until` is in the future. Use the provider's stable thread or conversation identifier as `session_id` when one exists. For Codex Desktop, use `$CODEX_THREAD_ID` and the verified deep-link format `codex://threads/<session_id>`. Use an optional `session_provider` such as `codex`, `claude`, or `chatgpt`, and store `session_url` only when the provider exposes a verified conversation URL. The owning session may renew or release its lease. Another worker may reclaim only an expired lease.

```bash
python3 scripts/task_lease.py claim work/ready/example.md --agent codex --session-id "$CODEX_THREAD_ID"
python3 scripts/task_lease.py renew work/in-progress/example.md --agent codex --session-id "$CODEX_THREAD_ID"
python3 scripts/task_lease.py release work/in-progress/example.md --agent codex --session-id "$CODEX_THREAD_ID"
python3 scripts/task_lease.py reclaim work/in-progress/example.md --agent claude --session-id "<claude-conversation-id>"
```

The helper uses a short-lived local lock at `work/.task-lease.lock` so two local workers cannot update leases simultaneously. If an interrupted process leaves the lock behind, confirm no lease update is running before removing that directory. Git remains the history layer; agents should still inspect repository state before committing.

Codex Desktop session links use `codex://threads/<session_id>`. For providers
without a verified URL scheme, show or copy the real thread ID until a verified
click-through URL is available.

## File Claims

Task leases identify task ownership. Before editing vault files, use
[[file-claim-ledger]] to declare the smallest practical file or directory set.

```bash
python3 scripts/file_claims.py status
python3 scripts/file_claims.py claim wiki/07-systems/example.md \
  --agent codex \
  --provider openai \
  --session-id "$CODEX_THREAD_ID" \
  --task-id task-YYYY-MM-DD-example
```

The Git-ignored local ledger annotates dirty files as `OWNED`, `SHARED`,
`EXPIRED`, or `UNCLAIMED`. An unclaimed dirty file has unknown ownership; it is
not safe to discard or absorb into a commit without inspection.

After validating a coherent slice, create a searchable attributed checkpoint
commit before continuing:

```bash
git add path/to/intended-file
python3 scripts/agent_commit.py checkpoint \
  --message "Checkpoint bounded workflow slice" \
  --agent codex \
  --provider openai \
  --session-id "$CODEX_THREAD_ID" \
  --task-id task-YYYY-MM-DD-example
```

Use `complete` for the final assigned outcome. The helper records `Agent`,
`Provider`, `Session`, `Task`, and `Commit-Type` Git trailers.

Treat `index.md`, `log.md`, and current handoff pages as short-lived shared
entry points. Claim them near the end of a coherent slice, selectively stage
only the intended hunk when parallel edits exist, commit promptly, and release
the claim.

## Activity Updates

Use a compact append-only section:

```markdown
## Activity

- 2026-05-30 14:00 | [codex:gpt-5](codex://threads/<session_id>) | Claimed task.
- 2026-05-30 14:18 | [codex:gpt-5](codex://threads/<session_id>) | Verified failure-path behavior.
- 2026-05-30 14:31 | [codex:gpt-5](codex://threads/<session_id>) | Ready for Leo review.
```

The author cell should be a Markdown link in the form
`[agent:model](session-deep-link)`. Use the current worker's actual model label
when known; otherwise use the provider's useful routing label. Record meaningful
state changes, discoveries, blockers, approvals, and completion. Do not stream
internal chain-of-thought or noisy progress chatter.

## Task Relationships

Parallel threads should be able to discover adjacent work even when a handoff is incomplete.

Use explicit relationships when a human or agent knows the coordination meaning:

```yaml
blocked_by:
depends_on:
blocking:
dependents:
related_tasks:
  - task-YYYY-MM-DD-slug
parent_task:
supersedes:
```

Relationship meanings:

```text
blocked_by     unresolved hard dependencies that currently prevent execution
depends_on     durable directional dependency history, including resolved dependencies
blocking       active inverse of blocked_by; unresolved downstream tasks waiting on this one
dependents     durable inverse of depends_on; downstream tasks that require this one
related_tasks  useful context or adjacent work, without ordering
parent_task    program, project, or umbrella task
supersedes     replaces an older task
```

When a dependency resolves, remove the active `blocked_by` / `blocking` pair
but retain the durable `depends_on` / `dependents` pair. Do not replace a
resolved directional dependency with nondirectional `related_to`.

Keep deterministic suggestions separate from explicit metadata. A report-only helper may rank likely related tasks using:

```text
shared wiki_page
shared source
shared parent_task
shared project or repo
shared tags
explicit wikilinks
matching blocked_by IDs
title keyword overlap
recent activity references
```

Suggested relationships are retrieval hints, not dependencies. Do not auto-write `blocked_by`, merge tasks, or assign workers based only on similarity.

Each task packet should include:

```text
explicit depends_on, dependents, and related tasks
blocking and blocked tasks
dependency changes that may alter current assumptions
top suggested related tasks with reasons
recent activity from those tasks
required policy links for the selected task surface
```

## Compact Work Packets

Dispatch agents with:

```text
task
definition of done
relevant vault links
recent task activity
approval boundary
output destination
required policy links
```

Use [[queue-worker-bootstrap]] when a fresh worker is asked to pick up queued
work without a named task.

After a context cutoff, usage limit, provider switch, or interrupted session,
generate a bounded recovery map before loading deeper context:

```bash
python3 scripts/recent_work_packet.py
```

Use [[recent-work-takeover-packet]] for the selective-reading sequence. The
packet is a retrieval map, not permission to bulk-read the vault.

Do not send full Slack threads or the whole vault to every agent.

## Approval Boundary

Require Leo approval before:

- publishing or sending externally
- changing pricing, public copy, or brand rules
- crossing private/public audience boundaries
- installing third-party code or skills
- spending money
- deleting durable source material
- allowing agents to create more agents
- granting broad secret access

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[task-system]]
- related_to: [[agent-control-plane-operating-model]]
- related_to: [[autonomous-agent-heartbeats]]
- related_to: [[slack-agent-command-center]]
- related_to: [[task-dashboard]]
- related_to: [[deterministic-automation]]
- related_to: [[agent-system]]
- related_to: [[agent-role-registry]]
- related_to: [[file-claim-ledger]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[agent-presence-ledger]]
