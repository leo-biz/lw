---
title: Provider Usage And Context Limit Direction
node_type: direction
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - usage-limits
  - context-windows
  - budgets
  - handoffs
  - ai-reviewed
created: 2026-06-01
updated: 2026-06-06
---

# Provider Usage And Context Limit Direction

## Decision

Treat provider headroom as an optional preflight input, not as the source of
truth for continuation. Every worker should checkpoint before provider limits
force an abrupt stop. Continue into a second task only when the next bounded
slice, validation, and handoff reserve fit with margin.

Do not build automation that scrapes personal subscription dashboards or stores
new provider secrets in the vault. Prefer runtime-native status, API response
headers, provider admin APIs when already authorized, and conservative fallback
questions.

## Limit Types

| Limit | Meaning | Typical evidence |
|---|---|---|
| subscription allowance | included product usage over a rolling or weekly window | product UI, runtime command, warning banner |
| API rate limit | requests or tokens allowed over short intervals | response headers, provider console, rate-limit API |
| API spend limit | maximum billable use over a billing period | provider console, admin usage and cost API |
| context window | maximum tokens one model request can carry | model docs or model-capability API |
| output-token limit | maximum tokens one model response can produce | model docs or model-capability API |
| runtime session limit | tool-specific cap, expiry, or interruption boundary | runtime docs and observed behavior |

These limits are independent. Remaining context does not imply remaining
subscription allowance, API throughput, spend budget, or runtime time.

## Provider Comparison

Verified against primary sources on 2026-06-01:

| Surface | Current facts | Useful signal | Reliability |
|---|---|---|---|
| Codex with ChatGPT plan | Plan-dependent agentic allowance. Local messages and cloud tasks share a five-hour window; additional weekly limits may apply. Task complexity, context size, model, local or cloud execution, speed mode, and image generation affect consumption. | Codex usage dashboard; CLI `/status` for remaining limits in an active CLI session; limit banner near exhaustion. | Interactive. No documented personal allowance API. |
| Codex Desktop thread | Thread runtime may expose goal elapsed time and a completion budget when available. | Runtime goal-status read. | Observed as optional: this thread returned no active goal and no budget report. |
| ChatGPT | Product limits vary by plan, model, and feature. Claude-style universal message math does not apply. | Product UI and model picker where exposed. | Interactive and changeable; do not hardcode a single allowance. |
| OpenAI API | Organization and project rate limits vary by model and usage tier. Monthly API usage limits are separate from ChatGPT-plan Codex allowances. | Response usage fields; `x-ratelimit-*` response headers; organization usage and costs API; account Limits page. | Machine-readable with authorized API access. |
| Claude subscription surfaces | Claude.ai, Claude Code, and Claude Desktop draw from the same subscription usage allowance. Plans differ; conversation length, complexity, features, and model affect use. | Claude Code `/usage`; `rate_limits` custom status-line fields; Claude Desktop usage ring; reset warning. | Interactive. Do not assume a fixed number of messages. |
| Claude Code with API key | Token-billed API usage rather than subscription allowance. | Claude Code `/cost` for session spend; provider API signals below. | Interactive plus API-readable. |
| Anthropic API | Organization and optional workspace spend and rate limits. Messages API rate limits use RPM, ITPM, and OTPM; token-bucket replenishment can make burst behavior matter. | `anthropic-ratelimit-*` response headers; `retry-after`; Console Usage page; Rate Limits API; Usage and Cost Admin API with admin key. | Machine-readable with authorized API access. |
| Local `ccusage` tool | Installed at `/opt/homebrew/bin/ccusage`. It reads local coding-agent usage logs for supported CLIs, including Codex and Claude Code. | `ccusage codex daily`, `ccusage codex session`, `ccusage claude daily`, `ccusage claude session`, `ccusage claude blocks --active`, and `ccusage claude blocks --recent`. | Local and useful for token/session accounting. It does not by itself prove provider-side remaining subscription allowance unless the local logs and block projections expose enough evidence. |

Low-cost Slack classification providers remain documented in
[[llm-routing-and-token-reduction]]. They are API routing inputs, not the
interactive worker-runtime baseline for this guide.

## Context Capacity

Context windows and maximum output tokens are model-dependent and change over
time. Query provider model documentation or capability APIs instead of copying
one value into the workflow:

- OpenAI model pages expose context windows, max output tokens, and tiered rate
  limits per model.
- Anthropic's Models API exposes `max_input_tokens`, `max_tokens`, and model
  capabilities. Anthropic also documents token counting before a request.
- Claude Code automatically compacts near context pressure; that reduces abrupt
  failure risk but does not replace checkpoints.
- Reasoning tokens can consume context and billing capacity even when they are
  not fully visible to an API caller.

## Durable Facts And Reverification

Durable:

- subscription usage is separate from API usage
- rate limits are separate from spend limits
- context windows and output caps are model-specific
- runtime-native signals are preferable to scraping
- checkpoints must not depend on perfect prediction

Reverify periodically:

- plan allowances, rolling windows, and weekly caps
- model IDs, context windows, output caps, and tier tables
- credit purchasing and flexible-pricing behavior
- runtime commands, UI rings, and status-line fields
- availability and freshness of provider usage APIs

## Conservative Preflight

Before substantial work or another task, ask:

```text
task or phase:
bounded outcome:
estimated execution time:
validation and handoff reserve:
lease time remaining:
context headroom signal:
subscription or API headroom signal:
cost allowance signal:
approval boundary:
can this finish or checkpoint safely with margin:
```

When exact usage is unavailable:

1. Treat headroom as unknown, not unlimited.
2. Prefer one bounded coherent slice.
3. Keep at least 20% of the estimated session time or 10 minutes, whichever is
   larger, for validation, Activity, lease handling, and handoff.
4. Checkpoint before loading another large context packet, starting a broad
   test suite, or claiming a related task.
5. Stop rather than continue when the estimate is uncertain.

For unattended heartbeat workers, start stricter:

- `max_tasks: 1`
- explicit `max_minutes`
- `shutdown_reserve_minutes: 5` or more
- provider-specific token or cost ceiling when the runner can observe it
- stop when the signal is absent and the next phase is not obviously bounded

## Safe Automation Opportunities

Allowed first:

- surface runtime-native status commands in an operator card
- use `ccusage` for local Codex and Claude Code token/session reports before
  relying on provider dashboards
- record the worker's qualitative preflight result in the handoff checkpoint
- let API clients log response-header headroom without storing secrets in the
  vault
- query OpenAI organization usage or Anthropic Usage and Cost APIs only in a
  separately approved integration with secrets outside the vault

Do not:

- scrape personal subscription dashboards
- infer a universal remaining-message count from one runtime
- store API keys, admin keys, cookies, or account exports in the vault
- block recovery on a usage API being available

## Recommended First Slice

Add a compact provider-budget preflight operator card and link it from the
queue-worker bootstrap and heartbeat protocol. Keep the first implementation
documentation-only. A later reviewed runner slice may add structured preflight
fields and API-header logging.

## Validation

1. Review the operator card against the provider sources below.
2. Exercise Codex CLI `/status` and Claude Code `/usage` interactively.
3. Confirm unknown headroom produces a conservative stop or checkpoint.
4. Confirm no secrets, cookies, or scraped account data enter the vault.
5. Validate wikilinks and inspect the staged diff.

## Primary Sources

- Codex pricing and limits: https://developers.openai.com/codex/pricing
- Using Codex with your ChatGPT plan: https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- OpenAI API rate limits: https://developers.openai.com/api/docs/guides/rate-limits
- OpenAI organization usage API: https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage
- Claude usage and length limits: https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work
- Claude Code error reference: https://code.claude.com/docs/en/errors
- Claude Code costs: https://code.claude.com/docs/en/costs
- Anthropic API rate limits: https://platform.claude.com/docs/en/api/rate-limits
- Anthropic Usage and Cost API: https://platform.claude.com/docs/en/manage-claude/usage-cost-api
- Anthropic models overview: https://platform.claude.com/docs/en/docs/about-claude/models
- Anthropic context windows: https://platform.claude.com/docs/en/build-with-claude/context-windows

## Linked Nodes

- implements: [[autonomous-agent-heartbeats]]
- related_to: [[recent-work-takeover-packet]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[codex-claude-goal-loop-continuation-direction]]
