---
title: Agent Authority Policy
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - safety
  - approvals
  - slack
  - ai-reviewed
created: 2026-06-04
updated: 2026-06-04
---

## Purpose

Define what actions agents may take in each operating mode, and what
gate — if any — is required before proceeding. This table is the single
source of truth for the enforcement helper (`scripts/authority_policy.py`)
and for any future control-plane surface that routes work to agents.

Use [[agent-control-plane-operating-model]] for the broader vocabulary of
modes, sessions, workers, and approval gates.

## Authority Levels

Actions are assigned one of ten authority levels ordered by risk and
reversibility. Higher levels require higher-authority modes and stronger
gates.

| Level | Name | Examples |
|-------|------|---------|
| L0 | read-only | read vault, search, list tasks, get status |
| L1 | suggest | draft reply, suggest task, create report, LiteLLM classify, dispatcher thread reply |
| L2 | create-task | write a new READY task file |
| L3 | claim-task | claim task lease, update task status, append activity within active lease |
| L4 | edit-vault | edit wiki pages, edit non-task vault files |
| L5 | commit | git commit, git push |
| L6 | send-slack | post to new Slack channels or DMs (not dispatcher-owned threads) |
| L7 | spend-api | BriefKit worker launch, paid subscription usage |
| L8 | delete-archive | delete files, archive tasks, prune presence records |
| L9 | publish-export | external sends, mark HUMAN_REVIEWED, move to exports/, install software, change credentials, grant broad access, launch autonomous loops |

## Mode Ceilings

Each operating mode has a maximum authority level. Actions above the ceiling
are **denied outright** — no gate can elevate them.

| Mode | Max Level | What is allowed |
|------|-----------|----------------|
| `chat` | L1 suggest | Read vault, draft replies, LiteLLM classification, dispatcher thread replies |
| `task_command` | L3 claim-task | All of chat + create tasks and claim task leases (reaction gate required for L2–L3) |
| `worker` | L5 commit | All of task_command + edit vault files and commit (explicit-text gate required for L4–L5) |
| `review` | L4 edit-vault | Read + annotate wiki; no commits |
| `ask_many` | L4 edit-vault | Report-only multi-model review; same ceiling as review |
| `scheduled_automation` | L6 send-slack | Pre-approved Slack writes in dispatcher-owned threads only |

## Approval Gates

When an action is within the mode ceiling but still requires approval before
proceeding, the gate type determines how that approval is collected:

| Gate | Meaning | How it is collected |
|------|---------|-------------------|
| `none` | Proceed immediately | No approval needed |
| `reaction` | Slack 👍 reaction | Post approval prompt; wait for `+1`/`thumbsup`/`white_check_mark` reaction |
| `explicit_text` | Explicit text confirmation | Post prompt; wait for explicit text reply (not a reaction) |
| `leo_review` | Leo must review | `leo_review_required: true` on the task; do not proceed until Leo confirms |

## Action Registry

The complete table lives in `scripts/authority_policy.py` as `ACTION_REGISTRY`.
Key entries by gate type:

**No gate (L0–L1):**
- `read_vault`, `search_vault`, `list_tasks`, `get_task_status`
- `draft_reply`, `suggest_task`, `create_report`, `litellm_classify`
- `send_slack_reply` — dispatcher-owned thread replies (L1)
- `update_task_activity` — appending activity within an active lease (L3, no gate)

**Reaction gate:**
- `create_task` (L2) — write a new READY task file
- `claim_task` (L3) — claim a task lease
- `update_task_status` (L3) — change task status
- `archive_task` (L8) — archive or move a task to done *(no current mode ceiling covers this; requires future admin mode)*
- `prune_presence` (L8) — prune stale agent presence records *(same caveat)*

**Explicit-text gate:**
- `edit_wiki` (L4), `edit_vault_file` (L4) — edit vault content
- `git_commit` (L5), `git_push` (L5) — write to git history
- `send_slack_broadcast` (L6) — post to a new channel or DM
- `briefkit_launch` (L7) — start a BriefKit worker session

**Leo review required (L9):**
- `publish_export`, `mark_human_reviewed`, `send_external`
- `install_software`, `change_credentials`, `grant_broad_access`
- `launch_autonomous_loop`

## Dispatcher Integration

`scripts/slack_dispatcher.py` calls `check_action(action, mode)` at the top
of each Slack command handler. The result determines the path:

```python
result = check_action("create_task", "task_command")

if not result.allowed and not result.requires_gate:
    # Ceiling-denied — post failure_message and return.

if result.requires_gate and result.gate == ApprovalGate.REACTION:
    # Post approval prompt, register pending record, wait for reaction.

# result.allowed is True — proceed immediately.
```

The existing Slack reaction approval loop handles the `reaction` gate. Explicit-text
and Leo-review gates are not yet wired for Slack commands — actions requiring them
must be initiated outside Slack until the control plane expands.

## Failure Messages

When an action is denied, the dispatcher surfaces the `failure_message` from the
registry. Examples:

| Action | Failure message |
|--------|----------------|
| `create_task` in `chat` mode | ❌ 'Write a new READY task file to the vault' is not permitted in chat mode. |
| `create_task` awaiting reaction | ❌ Task creation requires 👍 approval first. |
| `edit_wiki` in `task_command` mode | ❌ 'Edit existing wiki pages' is not permitted in task_command mode. |
| `mark_human_reviewed` in any mode | ❌ 'Mark content HUMAN_REVIEWED' is not permitted in \<mode\> mode. |
| Unknown action | ❌ Unknown action 'X'. Register it in authority_policy.ACTION_REGISTRY first. |

## Remaining Manual Approval Gates

The following consequential actions have no automated enforcement yet and rely
on Leo reviewing the task or approving via Slack before the operator proceeds:

- **Explicit-text confirmation** for vault edits and commits via Slack — not yet
  wired into the dispatcher's approval loop; currently only reaction gates are
  collected.
- **BriefKit worker launches** (`briefkit_launch`, L7) — authority check is in
  the registry but the Slack-to-BriefKit adapter does not exist yet; approval
  happens out-of-band until [[select-and-build-first-worker-adapter]] is done.
- **Broad Slack permission expansion** — adding `channels:history`, private channel
  scopes, or DM access requires Leo approval recorded in [[slack-agent-command-center]].
- **Any new action** not yet in `ACTION_REGISTRY` — defaults to leo_review gate
  via `check_action`; must be explicitly registered before it can be used.

## Linked Nodes

- implements: [[agent-control-plane-operating-model]]
- implements: [[slack-agent-command-center]]
- related_to: [[multi-agent-coordination]]
- related_to: [[agent-role-registry]]
- enforcement: `scripts/authority_policy.py`
- tests: `scripts/tests/test_authority_policy.py`
