---
title: File Claim Ledger
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - coordination
  - git
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# File Claim Ledger

## Purpose

Make live uncommitted work attributable without guessing from Git diffs.

Task leases answer who owns a task. The local file-claim ledger answers which
active session expects to modify a dirty file or directory.

## Local Ledger

The deterministic helper stores live claims in:

```text
work/.file-claims.json
```

The ledger is Git-ignored because claims are temporary local coordination state.
Git commits, Markdown tasks, checkpoints, and Activity remain the durable
history.

## Declare Before Editing

Claim the smallest practical set of files or directories before editing:

```bash
python3 scripts/file_claims.py claim \
  wiki/07-systems/example.md scripts/example.py \
  --agent codex \
  --provider openai \
  --session-id "$CODEX_THREAD_ID" \
  --task-id task-YYYY-MM-DD-example
```

Use a directory claim for a bounded batch. Avoid broad claims such as the vault
root. Claims expire after two hours by default and can be renewed by claiming
the same path again.

An overlapping active claim from another session fails by default. Use
`--allow-shared` only when the agents intentionally coordinate on a shared file.

## Inspect Dirty Ownership

Before editing shared files, staging, committing, or taking over interrupted
work:

```bash
python3 scripts/file_claims.py status
```

Each dirty file is labeled:

```text
OWNED      one active session declared the file
SHARED     overlapping work was declared intentionally
EXPIRED    a prior claim exists but its lease elapsed
UNCLAIMED  no session declared responsibility
```

Treat `UNCLAIMED` as unknown ownership, not permission to edit or discard the
change. Inspect recent task Activity or ask Leo when attribution matters.

## Dirty Target Deferral

Sometimes the obvious file for a useful improvement is already dirty, claimed,
expired, unclaimed, or mixed with another worker's unfinished slice. Do not
opportunistically edit that file just because the change would be helpful.

Use this decision rule:

1. If the dirty target is not required for the current Definition of Done,
   defer that part and keep the current slice scoped to clean or owned files.
2. If the dirty target is required, inspect Activity, claims, and Git history;
   then ask Leo or perform an explicit takeover only when the policy allows it.
3. If the dirty target would be useful but is not blocking, create or update a
   follow-up task or handoff instead of touching the file.
4. Record the deferred scope in task Activity and Review Proof residual risk.
5. Use path-scoped staging and attributed commits for only the files owned by
   the current session.

This applies even when the deferred change is a natural enforcement surface,
dashboard hook, documentation cross-link, or cleanup. Preserving ownership is
more important than folding every adjacent improvement into one commit.

## Release

Release claims after committing, handing off, or stopping:

```bash
python3 scripts/file_claims.py release --session-id "$CODEX_THREAD_ID"
```

Remove expired local records when useful:

```bash
python3 scripts/file_claims.py prune
```

## Agent Rule

Every vault-editing agent should:

1. inspect `git status --short`
2. run `python3 scripts/file_claims.py status`
3. declare intended file claims before editing
4. preserve files claimed by other active sessions
5. stage only its own edits
6. release its claims after commit or durable handoff

## Attributed Checkpoint Commits

Do not leave a coherent finished slice staged or uncommitted while continuing
into more work. Validate it, stage explicit files, create an attributed
checkpoint commit, release claims that are no longer needed, and continue only
when the next bounded slice fits safely.

```bash
git add path/to/intended-file
python3 scripts/agent_commit.py checkpoint \
  --message "Checkpoint bounded workflow slice" \
  --agent codex \
  --provider openai \
  --session-id "$CODEX_THREAD_ID" \
  --task-id task-YYYY-MM-DD-example \
  --path path/to/intended-file
```

Use `complete` instead of `checkpoint` when the assigned outcome is finished.
The helper requires an explicitly staged slice and adds searchable Git trailers:

```text
Agent: codex
Provider: openai
Session: <thread-id>
Task: task-YYYY-MM-DD-example
Commit-Type: checkpoint
```

Use a verified `--session-url` only when the provider exposes one.

Repeat `--path` for every intended file when concurrent agents may have staged
work. Path-scoped commits preserve unrelated staged files and reject intended
paths with newer unstaged edits. Omitting `--path` retains the whole-index mode
for a verified private index.

Codex sandbox policy may block Git index writes with
`.git/index.lock: Operation not permitted`. Treat that as an environment
approval boundary: rerun the exact `git add` or `agent_commit.py` command with
the required approval. It is not evidence of a vault lock defect.

After the completion commit, close the **task lease** as a separate step.
Check `leo_review_required` on the task and choose the right verb:

```bash
# Finished, no Leo sign-off needed — mark DONE and move to work/done/
python3 scripts/task_lease.py complete \
  work/in-progress/example.md \
  --agent codex --session-id "$CODEX_THREAD_ID"

# Finished, Leo must review — mark REVIEW and move to work/review/
python3 scripts/task_lease.py submit \
  work/in-progress/example.md \
  --agent codex --session-id "$CODEX_THREAD_ID"

# Yielding unfinished work — return to work/ready/ for another agent
python3 scripts/task_lease.py release \
  work/in-progress/example.md \
  --agent codex --session-id "$CODEX_THREAD_ID"
```

`complete` will error if `leo_review_required: true` and tell you to use
`submit` instead. Task IDs are accepted in place of file paths for all three.

## Shared Entry Points

Treat `index.md`, `log.md`, and current handoff pages as short-lived shared
entry-point edits:

1. claim the shared file only near the end of a coherent slice
2. inspect for active or unclaimed edits before changing it
3. selectively stage only the intended hunk when mixed changes already exist
4. commit promptly and release the claim

Prefer domain indexes and generated views as the vault grows. The root
`index.md` should remain a compact map, not a high-churn task database.

## Verify

```bash
python3 -m unittest scripts.tests.test_file_claims scripts.tests.test_agent_commit scripts.tests.test_task_lease -v
```

Before committing shared helper behavior:

```bash
python3 -m unittest discover -s scripts/tests -v
```

## Linked Nodes

- implements: [[multi-agent-coordination]]
- related_to: [[task-system]]
- related_to: [[recent-work-takeover-packet]]
- related_to: [[test-discovery-convention]]
