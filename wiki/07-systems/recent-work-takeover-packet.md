---
title: Recent Work Takeover Packet
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
  - handoff
  - context-engineering
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

## Purpose

Give a fresh AI worker a compact retrieval map after a context cutoff, usage
limit, provider switch, or interrupted session. The packet gathers recent
committed and uncommitted work without asking the next worker to bulk-read the
vault.

The Markdown vault, task Activity, handoff checkpoints, and Git remain the
sources of truth. The packet is a report-only index over them.

## Run

```bash
python3 scripts/recent_work_packet.py
```

Optional bounds:

```bash
python3 scripts/recent_work_packet.py \
  --since "5 days ago" \
  --max-commits 10 \
  --max-done 8 \
  --activity-lines 3
```

## Included Context

- Dirty Git worktree files, including staged, unstaged, and untracked files
- Recent commit summaries
- Tasks in `work/in-progress/`, `work/review/`, and `work/blocked/`
- Lease, owner, checkpoint, blocker, and recent Activity details when present
- A bounded list of recently done tasks
- A fresh-agent sequence that reinforces selective reading

## Context-Engineering Rules

1. Use the packet as a map, not as a replacement for source files.
2. Start with the one active task relevant to Leo's request.
3. Read that task's checkpoint and recent Activity before opening linked context.
4. Inspect diffs only for the files relevant to the resumed slice.
5. Use `sqz_read_file` for repeated or large reads.
6. Preserve unrelated dirty files and do not infer ownership from the report.
7. Update checkpoints after coherent slices because usage limits may interrupt without warning.

## Provider Usage Signals

Provider limits should trigger earlier checkpoints when the runtime can observe
them, but recovery must not depend on limit prediction.

### OpenAI API

API usage is separate from ChatGPT subscription usage. API responses report
token usage, and organization owners can query usage and costs through the
OpenAI Usage API. Rate-limit headers can support early checkpoint thresholds.

### Codex With A ChatGPT Plan

Codex usage depends on the plan and counts toward an agentic-usage limit. OpenAI
directs users who are approaching the limit to the Codex usage page or limit
banner. Local messages and cloud tasks share a five-hour window, and additional
weekly limits may apply. During an active Codex CLI session, `/status` shows
remaining limits. Plus and Pro users may be able to buy credits. OpenAI does not
document a public endpoint for a personal worker to query the remaining
ChatGPT-plan agentic allowance, so routine checkpoints remain mandatory.

### ChatGPT

ChatGPT limits are feature- and model-specific. Some model limits expose reset
information in the model picker. Do not hardcode a single ChatGPT allowance or
assume it applies to Codex.

### Claude Subscription Workers

Claude subscription usage is distinct from Anthropic API usage. Claude.ai,
Claude Code, and Claude Desktop draw from the same subscription allowance.
Treat any visible session or weekly warning as an additional handoff trigger,
not as the only safeguard. Claude Code `/usage`, the `rate_limits` custom
status-line fields, and the Claude Desktop usage ring can expose remaining
allowance interactively.

### Anthropic API

Anthropic API usage is separate from Claude subscription usage. Messages API
responses expose `anthropic-ratelimit-*` headers and `retry-after`. Organization
admins may use the Usage and Cost Admin API, and current configured rate limits
can be read programmatically. Keep admin keys outside the vault.

### Operating Rule

Provider-native signals may trigger an earlier checkpoint, but unknown headroom
is not unlimited headroom. Follow [[provider-usage-and-context-limit-direction]]
and stop before starting another substantial slice when execution, validation,
and handoff reserve do not fit with margin.

## Verify

```bash
python3 -m unittest scripts.tests.test_recent_work_packet -v
```

Before committing shared helper behavior:

```bash
python3 -m unittest discover -s scripts/tests -v
```

## Primary Sources

- [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [Codex pricing and usage limits](https://developers.openai.com/codex/pricing)
- [Using Credits for Flexible Usage in ChatGPT](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro)
- [How do I check my token usage?](https://help.openai.com/en/articles/6614209-how-do-i-check-my-token-usage)
- [OpenAI o3 and o4-mini Usage Limits on ChatGPT and the API](https://help.openai.com/en/articles/9824962-openai-o1-o1-mini-and-o3-mini-usage-limits-on-chatgpt-and-the-api)
- [Claude usage and length limits](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work)
- [Claude Code error reference](https://code.claude.com/docs/en/errors)
- [Anthropic API rate limits](https://platform.claude.com/docs/en/api/rate-limits)
- [Anthropic Usage and Cost API](https://platform.claude.com/docs/en/manage-claude/usage-cost-api)

## Linked Nodes

- implements: [[multi-agent-coordination]]
- related_to: [[agent-completion-proof-protocol]]
- related_to: [[current-ai-takeover-handoff]]
- related_to: [[task-system]]
- related_to: [[test-discovery-convention]]
