---
title: LLM Routing and Token Reduction
node_type: reference
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - llm
  - routing
  - token-reduction
  - cost-optimization
  - infrastructure
  - ai-reviewed
created: 2026-05-31
updated: 2026-06-04
---

# LLM Routing and Token Reduction

## Routing Tools (2026)

| Tool | Approach | Self-host | Best for |
|------|----------|-----------|----------|
| **LiteLLM** | Proxy + rule-based routing, budget enforcement | Yes | Starting point — 100+ providers, spend caps, OpenAI-compatible |
| **RouteLLM** | ML classifier: strong vs. weak model per prompt | Yes | Pair with LiteLLM for smarter routing |
| **OpenRouter** | Cloud API aggregator | No | Easiest multi-model access without running infra |
| **Portkey** | Gateway + observability + fallbacks | Partial | Teams needing cost dashboards |

**Standard 2026 pattern:** LiteLLM as proxy layer + RouteLLM as routing brain.

## Adjacent Tool Evaluation

Evaluated on 2026-05-31 from primary sources:

| Tool | Recommendation | Why |
|------|----------------|-----|
| [9Router](https://github.com/decolua/9router) | Defer for current Slack API path; compare later for worker/session routing | It is a local OpenAI-compatible gateway and dashboard aimed at connecting CLIs/IDEs and custom clients to many upstream providers. Its architecture docs describe `/v1/*` compatibility APIs, provider translation, model and account fallback, OAuth/API-key provider management, usage tracking, local persistence, and optional cloud sync. Its product site emphasizes Claude Code, Codex CLI, Cursor, Copilot, and subscription-tier fallback. That makes it more relevant to the future worker-adapter/session-control plane than to the narrow Slack intent-classification API route. |
| [TencentDB Agent Memory](https://github.com/Tencent/TencentDB-Agent-Memory) | Defer; borrow patterns | It adds symbolic short-term offload, layered L0-L3 memory, SQLite + sqlite-vec retrieval, inspectable Markdown layers, and OpenClaw/Hermes adapters. Leo Life already has durable Markdown memory, sqz compression, compact packets, and explicit review gates. Revisit if runtime session recall or Hermes integration becomes a real gap. |
| [Zapier MCP](https://docs.zapier.com/mcp/quickstart) | Pilot later for selected actions | It exposes explicitly configured actions from connected apps through MCP and logs actions in Zapier history. This is the likely tool-connector path for Slack actions, not a model-provider plugin and not part of the initial LLM router. Start with a very small allowlist after the Slack approval loop is dependable. |
| [CloakBrowser](https://github.com/CloakHQ/CloakBrowser) | Defer | Drop-in Playwright replacement with a patched Chromium build for bot-detection resistance. There is no active blocked browser workflow that justifies adding it now. |
| [UI-TARS Desktop](https://github.com/bytedance/UI-TARS-desktop) | Defer | Mature multimodal desktop/browser automation stack with local and remote operators. Useful future option for supervised GUI work, but unrelated to the first low-cost routing and Slack slices. |

The transcript's generic "Agent Memory" label is inferred to refer to TencentDB
Agent Memory because its current repository positioning matches the described
short-term compression and long-term agent-memory claims. If the transcript
meant a different repository, evaluate that repository separately before
adoption.

### 9Router Versus LiteLLM

Fresh comparison checked on 2026-06-04 against LiteLLM docs, 9Router's site,
and 9Router's architecture page.

Both provide an OpenAI-compatible gateway and provider fallback, but they point
at different first jobs:

| Dimension | LiteLLM | 9Router |
|---|---|---|
| Primary fit | Production-style LLM API gateway/proxy | Local tool/provider routing gateway and dashboard |
| Current vault use | Slack intent routing through a stable OpenAI-compatible endpoint | Not in the current active path |
| Provider pattern | API-key/config-driven model routing across 100+ providers | OAuth and API-key provider connections, with emphasis on CLI/IDE tools and subscription/account fallback |
| Useful controls | Spend tracking, budgets, virtual keys, caching, retries, fallbacks, OpenAI-format translation | `/v1/*` compatibility APIs, model combos, account-level fallback, provider translation, usage/quota tracking, local persistence, optional cloud sync |
| Best next use | Keep as the default gateway for low-cost Slack/API calls | Evaluate after session manager and worker adapter design, especially for Codex/Claude Code/Cursor-style routing |
| Risk boundary | Narrower and already configured locally | Broader control plane; OAuth, account fallback, optional cloud sync, and IDE/MITM-style features need policy review before use |

Start with [LiteLLM](https://docs.litellm.ai/) because the current need is
narrow: Groq → Cerebras → approved low-cost complex tier, with budgets and a
stable endpoint for Slack. LiteLLM documents OpenAI-format access to 100+
providers, retry/fallback logic, spend tracking, budgets, caching, and a proxy
server.

9Router is worth a later sandboxed comparison if the system needs one local
endpoint for subscription-backed tools, CLI/IDE workers, account quota
fallback, provider/account dashboards, or format translation across Codex,
Claude Code, Cursor, and API providers. Do not treat it as a
prompt-complexity classifier; its documented strength is provider translation,
fallback, and tool routing.

**Current decision:** LiteLLM remains the default gateway for Slack/API model
calls. 9Router belongs in the future worker-adapter/session-control-plane
evaluation, not the first Slack chat or intent-routing path.

Current GitHub snapshot checked on 2026-05-31:

- 9Router: approximately 15.4k stars, 2.3k forks, and 63 releases; latest shown
  release `v0.4.63` dated 2026-05-26.
- TencentDB Agent Memory: approximately 4.5k stars, 374 forks, 75 commits, and
  7 releases; latest shown release `v0.3.6` dated 2026-05-28.

Stars are not adoption proof. The fork counts, releases, code surfaces, and
integration boundaries are more useful signals for this decision.

Primary sources checked on 2026-06-04:

- [LiteLLM docs](https://docs.litellm.ai/)
- [9Router architecture](https://github.com/decolua/9router/blob/master/docs/ARCHITECTURE.md)
- [9Router product site](https://9router.com/)

### Gateway Chaining

Provisional note from Leo-provided Google AI Mode chat history on 2026-06-04:
LiteLLM and 9Router can theoretically be chained because both expose
OpenAI-compatible endpoints. Verify exact config against primary docs before
implementation.

Useful patterns:

```text
App / Slack worker / API client
-> LiteLLM
-> 9Router
-> provider accounts
```

Use this when LiteLLM should remain the policy, budget, logging, and model-alias
front door, while 9Router handles local coding-tool provider/account fallback or
specialized compression underneath.

```text
Coding tool / local CLI
-> 9Router
-> LiteLLM
-> provider APIs
```

Use this only if a local coding tool benefits from 9Router's developer-facing
interface while still needing a shared LiteLLM backend.

Current boundary remains:

- Slack/API application routing: LiteLLM first.
- Local coding-tool subscription/account routing: evaluate 9Router later.
- Do not introduce chained gateways until a pilot proves the extra moving parts
  reduce real friction.

Compliance boundary:

- Do not build a system around bypassing subscription locks, resale controls, or
  consumer-account API restrictions.
- Treat claims that a local proxy can make consumer subscription use "look like"
  normal browser or terminal activity as a risk signal, not an implementation
  strategy.
- If 9Router or another proxy is evaluated, prefer documented, terms-compliant
  auth paths and keep the first pilot local, private, and reversible.

Operational note: when chaining gateways, test request metadata carefully.
LiteLLM may attach extra telemetry, client, or routing metadata that an
upstream/downstream OpenAI-compatible proxy does not accept. Use explicit model
aliases and config-level parameter filtering if a pilot shows `unknown
parameter` failures. Do not assume two OpenAI-compatible gateways are perfectly
transparent when chained.

### Slack Bus Backbone

For a Slack communication bus that classifies requests, pulls tasks from the
vault queue, posts updates, and uses cheap fallback models, LiteLLM remains the
best current backbone because the bus is a server-side application, not an IDE
extension.

Candidate route shape:

```text
Slack dispatcher / worker loop
-> LiteLLM model alias
-> Groq fast/default
-> Cerebras fallback
-> Gemini Flash for explicit complex or long-context work
```

The exact order should follow current provider limits, live test quality, and
cost. The Google AI Mode chat suggested Gemini-first with Cerebras/Groq fallback
in one pass and Groq-first in another; keep the vault's current Groq-first
decision until a fresh live comparison shows better quality/cost behavior.

For multi-agent chat, do not feed an entire shared channel into every model
call. Use thread isolation, explicit context packets, or branch-specific chat
state so each agent sees only the relevant sub-conversation plus durable task
context. This is a cost, latency, and hallucination-control requirement.

## Routing Strategies

| Strategy | How it works | When to use |
|----------|-------------|-------------|
| **Cost-based** | Cheap/simple → free/local models | Default starting strategy |
| **Latency-based** | Time-sensitive → Groq/Cerebras | Streaming chat, agent loops |
| **Capability-based** | Task type detection → specialist model | Code → Qwen-Coder, reasoning → DeepSeek-R1 |
| **Classifier-based** | ML scores prompt complexity → strong or weak | Best quality routing, RouteLLM |
| **Token-count threshold** | >N tokens → expensive model; else → cheap | Simple, effective, zero deps |

For the vault-level worker profile and task metadata convention, follow
[[worker-capability-routing]]. Route by truthful capabilities, tools, model
tier, cost tier, and approval boundary rather than provider brand alone.

## Token Reduction Strategies

### 1. Prompt Caching — highest ROI, enable first

| Provider | Savings | Notes |
|----------|---------|-------|
| Gemini | 75–90% | |
| OpenAI | 50% | Automatic on longer prompts |

LiteLLM can auto-inject caching checkpoints — turn on once, applies to all providers.

### 2. RAG Instead of Context Stuffing

Replace "send 50K tokens of docs" with "retrieve 2–5K relevant chunks."
Tools: LlamaIndex, ChromaDB, pgvector.
Typical reduction: 100K → 3K tokens per query.

### 3. Prompt Compression — LLMLingua-2

Compresses prompts 3–20x, 60–80% cost reduction on context-heavy workloads, near-zero quality loss.
Add after caching and RAG are in place.

### 4. Context/Memory Management

- **Rolling summary** — replace conversation history with distilled summary every N turns
- **MemGPT / Letta** — virtual paged memory for long-running agents; oldest context compressed and retrieved on demand

### 5. Structured Output

Force JSON / tool-use responses instead of prose — 20–40% output token savings consistently.

### 6. Batch APIs

- Best for: bulk classification, embedding generation, offline processing

### 7. Model Distillation (Advanced)

Use a large model to generate training data for a task-specific small model.
One-time training cost → zero marginal inference cost thereafter.

## Recommended Stack for Leo

```
Prompt → LiteLLM proxy (budget caps + provider normalization)
              ↓
         RouteLLM classifier (add after LiteLLM is stable)
         ├── fast/default  → Groq (Llama 70B, free, 500–800 tok/s)
         ├── fallback      → Cerebras (Llama 70B, 1M tokens/day free)
         └── complex/long  → Gemini Flash or another explicitly approved low-cost tier
```

**Note:** No local tier — Leo decision, M4 16GB at 30 tok/s too slow.

**Gateway boundary:** LiteLLM is the current model gateway for API-style calls.
9Router is a future candidate for tool/session routing when the worker adapter
layer needs to coordinate Codex, Claude Code, Cursor, or other subscription and
CLI-backed tools through one local endpoint.

**Runtime API boundary:** Do not use Anthropic API calls for routine routing or
Slack intent parsing. Keep the shared route OpenAI-compatible so Slack can use
the selected low-cost provider stack and the chosen provider-plugin or MCP
integration path.

For the control-plane boundary between cheap API model calls, subscription-backed
workers, Slack chat, and live session supervision, use
[[agent-control-plane-operating-model]].

## Decision: Groq-First Slack Routing

Decided on 2026-06-01: keep the verified Groq-first architecture as the default
Slack intent-classification path.

```text
Slack intent parsing
-> Groq llama-3.1-8b-instant
-> Cerebras gpt-oss-120b fallback

Explicit complex work
-> Gemini 2.5 Flash
```

Slack intent parsing is a small classification task. Prefer the fast, roomy
default before spending a more capable reasoning route on every message:

| Provider route | Use | Current documented rationale |
|---|---|---|
| Groq `llama-3.1-8b-instant` | Default Slack classifier | Approximately 560 tokens/sec. Groq's published free-plan limits show 30 RPM, 14.4K RPD, and 500K TPD. |
| Cerebras `gpt-oss-120b` | Automatic fallback | Cerebras' published free-tier limits show 30 RPM, 14.4K RPD, and 1M TPD. |
| Gemini `gemini-2.5-flash` | Explicit complex or long-context work | Google describes it as a low-latency, high-volume thinking model for agentic use cases. Its published free tier shows 10 RPM and 250 RPD, so do not spend it on every Slack classification by default. |

Treat provider limits as current operational inputs, not permanent facts.
Re-check them before changing routing policy.

If live Slack tests show that the 8B Groq model misclassifies natural-language
commands often enough to hurt the workflow, promote only the first tier to
Groq `llama-3.3-70b-versatile`. Groq currently documents that route at
approximately 280 tokens/sec with stronger general capability but tighter
free-plan limits: 30 RPM, 1K RPD, and 100K TPD.

Primary sources checked on 2026-06-01:

- [Groq models](https://console.groq.com/docs/models)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
- [Cerebras models](https://inference-docs.cerebras.ai/models/overview)
- [Cerebras rate limits](https://inference-docs.cerebras.ai/support/rate-limits)
- [Gemini models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

Store provider keys outside the vault in:

```text
~/.config/leo-life/llm/env
```

Use shell-compatible lines:

```text
GROQ_API_KEY='...'
CEREBRAS_API_KEY='...'
GEMINI_API_KEY='...'
```

Check presence without printing values, then run tiny live probes:

```bash
python3 scripts/check_free_llm_stack.py
python3 scripts/check_free_llm_stack.py --live
```

### LiteLLM Pilot Config

The committed pilot config is `config/llm/litellm.yaml`. It keeps secrets in
environment variables, exposes `fast`, `fast-backup`, and `smart` aliases,
enables a local LiteLLM cache, and routes `fast` failures to `fast-backup`.
Installing LiteLLM and starting the proxy remain approval-gated third-party
setup steps.

```bash
uv tool install --python /opt/homebrew/bin/python3.13 'litellm[proxy]'
python3 scripts/check_litellm_config.py
set -a
source ~/.config/leo-life/llm/env
set +a
litellm --config config/llm/litellm.yaml --port 4000
```

Use Python `3.13` for the local `uv` tool environment. LiteLLM `1.86.2`
installed under Python `3.14` pulled `uvloop==0.21.0`, which failed at proxy
startup because that dependency imports an asyncio symbol removed in Python
`3.14`. Reinstalling the same package under the already-installed Python `3.13`
runtime fixed the launch.

The committed structure follows LiteLLM's official documentation:

- [Proxy config](https://docs.litellm.ai/docs/proxy/configs)
- [Caching](https://docs.litellm.ai/docs/proxy/caching)
- [Fallbacks](https://docs.litellm.ai/docs/proxy/reliability)

## Verify

```bash
python3 -m unittest scripts.tests.test_check_litellm_config -v
python3 scripts/check_litellm_config.py
```

Before committing shared helper behavior:

```bash
python3 -m unittest discover -s scripts/tests -v
```

**Token reduction rollout order (by ROI):**
1. Prompt caching — instant savings, enable in LiteLLM config
2. RAG — for any doc-heavy or knowledge-base workflows
3. LLMLingua-2 — when context is still bloated after 1 and 2
4. Batch API — for any offline/async tasks

**Cost floor achievable:** $0/month for most personal workloads using Groq + Cerebras free tiers + prompt caching.

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[free-local-llms]]
- related_to: [[task-system]]
- related_to: [[worker-capability-routing]]
