---
title: Slack Dispatcher
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by: Claude
reviewed_date: 2026-05-31
audience: private/internal
tags:
  - systems
  - slack
  - ai-agents
  - playbook
  - ai-reviewed
created: 2026-05-31
updated: 2026-06-03
last_modified: 2026-06-03
---

## Purpose

`scripts/slack_dispatcher.py` is the local Socket Mode bridge between Slack and the Markdown task vault. Mention the bot in Slack to create or claim tasks, check status, and approve or reject pending actions via reactions.

Slack is the communication surface. Markdown tasks in `work/` remain the source of truth.

## Running

```bash
python3 scripts/slack_dispatcher.py
```

Tokens are loaded automatically from `~/.config/leo-life/slack/env`. The process connects via Socket Mode — no public URL or firewall rule needed.

Expected startup output:

```text
Slack dispatcher starting (Socket Mode)…
Vault: /path/to/LeoLife
Pending approvals loaded: 0
⚡️ Bolt app is running!
```

Stop with `Ctrl-C`.

## Commands

Mention the bot in any channel the bot has been invited to:

| Mention | What it does |
|---|---|
| `@leo-agent create task: <title>` | Creates a new READY Markdown task in `work/ready/` and posts a compact work packet |
| `@leo-agent claim task: <task-id>` | Finds a READY task by ID and prompts approval to move it to in-progress |
| `@leo-agent status` | Posts current task counts (Inbox / Ready / In Progress / Review / Blocked) |
| `@leo-agent chat: <message>` | Replies in-thread through the low-cost routed model without writing to the vault |
| `@leo-agent save this: <note>` | Requests approval to turn a read-only chat note into a READY task |
| `@leo-agent make this a task: <request>` | Requests approval to turn a chat request into a READY task |
| `@leo-agent help` | Posts command reference |

## Read-Only Chat Mode

Use `chat:` for normal conversation:

```text
@leo-agent chat: what should I do next on the Slack project?
```

Chat mode uses the same LiteLLM OpenAI-compatible route as intent parsing,
defaulting to `SLACK_CHAT_MODEL=fast`. It posts only a dispatcher-thread reply.
It must not create tasks, edit files, approve actions, launch workers, record
memory, or retain full Slack transcripts.

To preserve something from chat, use an explicit handoff:

```text
@leo-agent save this: LiteLLM and cheap models may handle more report-only review than expected.
@leo-agent make this a task: compare Groq and Cerebras on packet drafting.
```

The dispatcher will draft a task title and wait for 👍 before writing a READY
task. A 👎 reaction cancels with no vault change.

## Intent Parsing

The dispatcher understands natural language — you do not need to memorize exact command syntax.

**How it works:**

1. The mention text (after `@leo-agent`) is sent to the local LiteLLM OpenAI-compatible route with a compact classification prompt.
2. The routed model returns a JSON object with `intent` and any extracted entities (`title` for create, `task_id` for claim).
3. If the API call fails or returns `unknown`, the dispatcher falls back silently to the regex parser.

**Natural language examples that work:**

| What you type | Parsed as |
|---|---|
| `can you make a task to review my emails` | `create` → title: "review my emails" |
| `new task: write weekly report` | `create` → title: "write weekly report" |
| `add a task for testing the Slack bot` | `create` → title: "testing the Slack bot" |
| `take task task-2026-05-31-foo` | `claim` → task\_id: "task-2026-05-31-foo" |
| `how many tasks are in progress` | `status` |
| `what can you do` | `help` |

**Fallback:**

The regex parser (`COMMAND_RE`) remains the authoritative backup. If the routed endpoint is unavailable, returns an error, has no provider credits, or returns `unknown`, the dispatcher silently falls back and exact-syntax commands still work.

**Dependencies:**

- local LiteLLM proxy at `LITELLM_BASE_URL`, defaulting to `http://127.0.0.1:4000`
- `SLACK_INTENT_MODEL`, defaulting to the LiteLLM alias `fast`
- `SLACK_CHAT_MODEL`, defaulting to the LiteLLM alias `fast`
- provider keys in `~/.config/leo-life/llm/env`, loaded by the LiteLLM proxy rather than committed to the vault

**Tests:** `scripts/tests/test_slack_intent_parsing.py` — mocked routed-client tests plus optional live LiteLLM tests gated by `RUN_LIVE_LITELLM_INTENT_TESTS`.

**Routing decision:** Leo does not want Anthropic API usage for routine Slack
intent parsing. Use the selected OpenAI-compatible low-cost routed endpoint and
keep deterministic fallback parsing active.

## Approvals

After `create task` or `claim task`, the dispatcher posts a compact work packet and waits for a reaction. React to the bot's threaded approval prompt. Reactions on the original mention are also accepted for compatibility:

| Reaction | Outcome |
|---|---|
| 👍 | Approves — task stays READY (create) or moves to in-progress (claim) |
| 👎 | Rejects — no vault change, outcome recorded |

The handler accepts Slack's common thumb aliases (`+1`, `thumbsup`,
`thumbs_up`, `-1`, `thumbsdown`, `thumbs_down`) and logs a concise
`reaction_added` diagnostic with channel, item timestamp, normalized outcome,
and pending lookup result. Do not log tokens.

Consequential approvals and rejections are written back to the task's `## Activity` section.

Pending approvals survive restarts — state is persisted to `runs/slack-pending-approvals.jsonl`.

When the routed classifier is unavailable, the regex fallback still accepts
common natural phrases such as `make a task to review my emails`, `grab
task-2026-05-31-example`, and `show me what's active`.

## Thread Replies

The dispatcher accepts thread replies only in threads it owns (from a dispatcher-originated message). Top-level channel messages are ignored. Thread replies are noted but do not trigger automated actions — use reactions for approvals.

## Channels

The pilot uses three attention-boundary channels:

| Channel | Purpose |
|---|---|
| `#ai-general` | General task mentions and status queries |
| `#ai-approvals` | Approval prompts for sensitive or leo-review-required tasks |
| `#ai-activity` | Alerts and status updates from automated jobs |

## Token Storage

Tokens live outside the vault at `~/.config/leo-life/slack/env`:

```text
SLACK_APP_TOKEN='xapp-...'   # app-level token, connections:write scope
SLACK_BOT_TOKEN='xoxb-...'   # bot token
```

Never commit tokens to the vault.

## Scopes and Events

Current Slack app configuration:

```text
Bot scopes:       app_mentions:read, chat:write, reactions:read, channels:history
Bot events:       app_mention, reaction_added, message.channels
App-level scope:  connections:write
```

## Pending Approvals Log

`runs/slack-pending-approvals.jsonl` — Git-ignored. Each line is one approval record. Resolved entries carry `"resolved": true`. The dispatcher replays this file on startup to restore in-flight approvals.

## Architecture

```text
Slack mention or reaction
  -> Socket Mode WebSocket (slack-bolt)
  -> slack_dispatcher.py event handler
  -> parse command / reaction
  -> read/write work/*.md (same lock as task_lease.py and task_dashboard.py)
  -> append activity entry
  -> post Slack reply
```

The dispatcher shares the `work/.task-lease.lock` directory lock with `task_lease.py` and `task_dashboard.py`. Dashboard writes during an active lease will be rejected, and vice versa.

## Slice 2 — Provider Adapter (not yet built)

After Leo selects a provider, a thin adapter will create or steer a temporary worker thread and record the real `session_id`, `session_provider`, and `lease_until` on the Markdown task. The dispatcher core will not change.

## Verify

```bash
env -u ANTHROPIC_API_KEY python3 -m unittest scripts.tests.test_slack_intent_parsing -v
```

Before committing shared helper behavior:

```bash
env -u ANTHROPIC_API_KEY python3 -m unittest discover -s scripts/tests -v
```

## Linked Nodes

- implements: [[slack-agent-command-center]]
- related_to: [[task-system]]
- related_to: [[task-dashboard]]
- related_to: [[deterministic-automation]]
- related_to: [[multi-agent-coordination]]
