---
title: Agent Completion Proof Protocol
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - playbook
  - verification
  - ai-reviewed
created: 2026-05-31
updated: 2026-06-02
---

## Purpose

Give every worker a repeatable way to prove that work is complete. A task is not
done because files changed or a command exited successfully. The agent must
connect the requested outcome, the implementation, and observable evidence.

Use this protocol for code, automations, dashboards, and meaningful vault
workflow changes. Scale the evidence to the risk and blast radius.

## Required Sequence

1. Read the active task and restate the observable outcome.
2. Inspect the affected surface before editing. Preserve unrelated changes.
3. Make the smallest coherent change that satisfies the outcome.
4. Run the narrowest useful automated checks first.
5. Run broader regression checks when shared behavior changed.
6. Exercise the real user path when rendering, interaction, or integration matters.
7. Inspect `git status --short` and the relevant diff.
8. Run `python3 scripts/task_lifecycle_validator.py`, then compare each Definition of Done checkbox against evidence.
9. Record `## Review Proof` with DoD evidence and See It Work instructions.
10. Record the verification result in task Activity.
11. Commit the finished meaningful batch with explicit staging scope.

When adding or changing a deterministic helper, document its focused test
command near the workflow and follow [[test-discovery-convention]].

## Evidence Ladder

Use the lowest sufficient rung, then climb when risk requires it.

| Change | Minimum evidence |
|---|---|
| Markdown or metadata | Parse or lint where available; inspect the diff and links |
| Deterministic script | Focused automated test plus one representative CLI run |
| Shared task mutation | Focused tests, lock or concurrency checks where relevant, and status inspection |
| Dashboard or browser flow | Backend checks plus browser exercise of the actual interaction |
| External integration | Local validation, then one end-to-end test with Leo approval and secrets kept outside the vault |
| Bulk rewrite | Dry run, representative sample approval, invariant checks, file counts, and exact staging review |

## Browser Proof

For user-facing local dashboards:

1. Start or restart the local server after code changes.
2. Open the affected route in the in-app browser.
3. Exercise the changed interaction rather than only loading the page.
4. Confirm the backing Markdown or data file changed correctly.
5. Remove disposable QA records.
6. Check the browser console when frontend behavior changed.

## Review Proof

Before `submit` or `complete`, add a `## Review Proof` section to the task.
The section must connect every checked Definition of Done item to evidence and
must tell Leo how to see or rerun the result when the work has a visible or
runnable surface.

Use this structure:

```markdown
## Review Proof

### DoD Evidence

- DoD: <checkbox text>
  Evidence: <command, file, diff, linked note, run ID, or manual check>
  Result: <passed / completed / caveat>

### See It Work

- How Leo can inspect: <URL, command, file path, screenshot, or output>
- Live run status: <running now / can be started with command / not run because approval or secret needed / not applicable>
- Residual risk: <none, or exact unresolved caveat>
```

For runnable tools, dashboards, automations, generated artifacts, and external
integrations, prefer live proof Leo can inspect: a local URL, a command to
rerun, an output path, a screenshot, or an explicit approval boundary. For
research or markdown-only work, say why live proof is not applicable and point
to the reviewed page or diff.

## Completion Gate

Before calling a task complete, confirm:

- Every Definition of Done item has evidence.
- `## Review Proof` includes both `### DoD Evidence` and `### See It Work`.
- Tests and manual checks are recorded with their outcomes.
- Temporary QA artifacts are removed.
- `git status --short` contains no accidental files.
- Only intended files are staged.
- Any residual risk, skipped test, or required Leo approval is stated plainly.
- Any useful but deferred dirty-target work is named with its ownership reason.
- The task checkpoint and Activity leave a clean continuation point.

If any condition is false, report the task as in progress, blocked, or ready for
review. Do not manufacture certainty.

## End Of Work Checklist

Before leaving a completed task or coherent work session:

1. Run a brief memory check using [[agent-system#Memory Check]]. Preserve only
   future-useful decisions, tasks, findings, outputs, open questions, or changed
   context that are not already represented durably. For non-editing modes,
   produce a Vault Handoff when something should be saved.
2. Confirm the final task Activity entry records verification, residual risk,
   skipped checks, approvals still needed, and the next useful action when one
   exists. Its author cell should be a session deep link in the form
   `[agent:model](session-deep-link)`, such as
   `[codex:gpt-5](codex://threads/<session_id>)`.
3. Commit the finished bounded slice with explicit staging scope and attribution.
   Do not absorb unrelated dirty files.
4. Close the task lease as a separate step: use `complete` for `DONE`, `submit`
   for Leo `REVIEW`, or `release` only when yielding unfinished work back to
   `READY`.
5. Commit any durable task-closure bookkeeping created by the lease helper.
6. Release file claims and mark agent presence `end`, `wait`, `stop`, or `block`
   with the latest commit and a compact handoff checkpoint.
7. Confirm the local thread name is useful and scan-friendly. For Codex, check
   `~/.codex/session_index.jsonl` for the current `$CODEX_THREAD_ID` and rename
   the thread when Leo chooses a better label or the default title no longer
   matches the completed work.
8. Inspect `git status --short`, file-claim status, and the relevant task
   destination one last time. State any unrelated dirty files plainly.
9. Recommend a fresh role-specific thread when the task or coherent phase is
   complete, the role changes, or context has become noisy.

Use [[file-claim-ledger]] for claim release and attributed commits,
[[queue-worker-bootstrap]] for task-lease closing verbs, and
[[agent-presence-ledger]] for session shutdown.

### Exact Command Card

Use this directly for vault task work. Replace placeholders deliberately. Never
use `git add .` or absorb unrelated dirty files.

```bash
# Bind once. Reuse the same SID in every command.
SID="${CLAUDE_CODE_SESSION_ID:-${CODEX_THREAD_ID:-}}"
AGENT="codex"                 # e.g. codex or claude
PROVIDER="openai"             # e.g. openai or anthropic
TASK_ID="task-YYYY-MM-DD-slug"
TASK_FILE="${TASK_ID#task-????-??-??-}.md"

# Choose exactly one closure mode:
LEASE_VERB="complete"; TASK_DEST="done";   COMMIT_VERB="complete";   PRESENCE_ACTION="end"   # DONE
# LEASE_VERB="submit";   TASK_DEST="review"; COMMIT_VERB="complete";   PRESENCE_ACTION="wait"  # Leo REVIEW
# LEASE_VERB="release";  TASK_DEST="ready";  COMMIT_VERB="checkpoint"; PRESENCE_ACTION="stop"  # unfinished yield

# 1. Memory check: preserve only future-useful information not already durable.
# Review decisions, tasks, findings, outputs, open questions, and changed context.
# Update the relevant vault page, task Activity, log, or Vault Handoff only when needed.

# 2. Verify scope before committing.
git status --short
python3 scripts/file_claims.py status
git diff -- path/to/intended-file another/intended-file

# 3. Stage only the bounded slice and create the attributed completion commit.
git add path/to/intended-file another/intended-file
git diff --cached --check
git diff --cached --name-status
python3 scripts/agent_commit.py "$COMMIT_VERB" \
  --message "Complete bounded task outcome" \
  --agent "$AGENT" --provider "$PROVIDER" \
  --session-id "$SID" --task-id "$TASK_ID" \
  --path path/to/intended-file --path another/intended-file

# 4. Close the task lease with the selected verb.
python3 scripts/task_lease.py "$LEASE_VERB" "$TASK_ID" \
  --agent "$AGENT" --session-id "$SID"

# 5. If lease closure changed a tracked task file, commit that bookkeeping.
git status --short
git add "work/in-progress/$TASK_FILE" "work/$TASK_DEST/$TASK_FILE"
git diff --cached --check
git diff --cached --name-status
python3 scripts/agent_commit.py "$COMMIT_VERB" \
  --message "Close task lease bookkeeping" \
  --agent "$AGENT" --provider "$PROVIDER" \
  --session-id "$SID" --task-id "$TASK_ID" \
  --path "work/in-progress/$TASK_FILE" --path "work/$TASK_DEST/$TASK_FILE"

# 6. Release local claims and close presence.
python3 scripts/file_claims.py release --session-id "$SID"
python3 scripts/agent_presence.py "$PRESENCE_ACTION" \
  --session-id "$SID" \
  --last-commit "$(git rev-parse --short HEAD)" \
  --handoff-checkpoint "Outcome, residual risk, and next useful action."

# 7. Confirm the local thread name is useful.
# For Codex, inspect ~/.codex/session_index.jsonl for $CODEX_THREAD_ID.
# If Leo provides a better name, update every row for the current session ID.

# 8. Final proof: state unrelated dirty files plainly.
git status --short
python3 scripts/file_claims.py status
python3 scripts/agent_presence.py status
```

If step 5 has no tracked bookkeeping changes, skip its `git add` and commit.
Use repeated `--path` arguments when the Git index may be shared with another
worker. If Codex sandbox policy blocks `.git/index.lock`, rerun the exact Git
write command with approval; do not treat that environment boundary as a vault
helper defect.

Task-folder wikilinks can become stale when a task moves between lifecycle
directories. After closing a lease, use the wiki health check to report broken
links and repair affected body-level links selectively. Do not auto-rewrite
arbitrary Markdown references during a lease transition. When resolving a hard
dependency, remove the active reciprocal `blocked_by` / `blocking` pair while
preserving durable reciprocal `depends_on` / `dependents` history.

For an unresolved blocker that should remain `IN_PROGRESS`, checkpoint the
slice, renew the task lease when appropriate, release file claims, and run:

```bash
python3 scripts/agent_presence.py block \
  --session-id "$SID" \
  --last-commit "$(git rev-parse --short HEAD)" \
  --handoff-checkpoint "Blocker, evidence, and the next action needed."
```

## Linked Nodes

- implements: [[task-system]]
- related_to: [[multi-agent-coordination]]
- related_to: [[deterministic-automation]]
- related_to: [[recent-work-takeover-packet]]
- related_to: [[test-discovery-convention]]
