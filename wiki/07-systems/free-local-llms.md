---
title: Free and Local LLMs
node_type: reference
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - llm
  - local-ai
  - infrastructure
  - compute
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
---

# Free and Local LLMs

## Leo's Hardware

**Mac Mini M4 base, 16GB unified memory.**
Viable local model range: 7B–9B. 13B is borderline (~15 tok/s). 27B+ not practical. Use free cloud inference for anything requiring 70B-class quality.

## SOTA Open-Weight Models (May 2026)

The gap between open-source and proprietary models has largely closed for most tasks.

| Model | Size | Strengths | License |
|-------|------|-----------|---------|
| **GLM-5.1** | 744B MoE (40B active) | Coding, reasoning, agentic; leads SWE-bench Pro | Open |
| **Kimi K2.6** | MoE | Best coding on LiveBench (78.57), multi-agent pipelines | Open |
| **Qwen3.7 Max** | — | 262K–1M context, top open-source quality index | Apache 2.0 |
| **Gemma 3 27B** | 27B | Beats Llama 405B and DeepSeek-V3 on LMArena | Apache 2.0 |
| **DeepSeek V3/R1** | MoE | Reasoning, math, code; MIT license | MIT |
| **Llama 3.3 70B** | 70B | General, instruction following; runs free on Groq/Cerebras | Llama |
| **Qwen2.5-Coder 32B** | 32B | Best dedicated code model under 70B | Apache 2.0 |
| **Phi-4** | 14B | Strong for size, good on CPU/low-RAM | MIT |

## Best Local Models for M4 16GB

| Model | Tok/s | Use for |
|-------|-------|---------|
| `gemma3:9b` | ~30–35 | Best quality at this size; general use |
| `llama3.2` (8B) | ~30–35 | Fast general use, well-supported |
| `qwen2.5-coder:7b` | ~35 | Local code tasks |
| `phi4:14b` | ~15 | Higher quality, slower — only if speed is acceptable |

## Free Cloud Inference (Primary Tier)

Use these as the default — faster than local and free.

| Provider | Free Tier | Speed | Best for |
|----------|-----------|-------|----------|
| **Groq** | Generous daily limits on Llama 3.3 70B | 500–800 tok/s | Primary fast inference |
| **Cerebras** | 1M tokens/day on Llama 3.1 70B | Very fast | High-volume backup |
| **Google AI Studio** | 1,500 req/day on Gemini Flash | Fast | Long-context tasks |

## Recommended Inference Stack

**Decision: cloud-only.** M4 16GB runs 7B–9B at ~30 tok/s — too slow. Groq/Cerebras are faster and free.

```
Default      → Groq (Llama 3.3 70B, free, 500–800 tok/s)
Fallback     → Cerebras (Llama 70B, 1M tokens/day free)
Complex/long → Claude Sonnet (with prompt caching)
```

If private/sensitive data handling becomes a requirement in the future, revisit adding a local tier.

## Runtimes

| Runtime | Best for |
|---------|----------|
| **Ollama** | Daily use — easiest, REST API on :11434, MLX-backed on Apple Silicon |
| **LM Studio** | Trying models before committing |
| **Jan** | Local agent workflows, OpenAI-compatible API |

Ollama now uses Apple's MLX framework on Apple Silicon by default (30–50% faster than llama.cpp).

## Quantization Reference

| Format | Quality | Size (7B) | Use when |
|--------|---------|-----------|----------|
| Q4_K_M | Good | ~4.5 GB | Default — best quality/size balance |
| Q8 | Excellent | ~8 GB | Enough RAM, want near-full quality |
| F16 | Full | ~14 GB | Research only |

## Paid Fallback

- **DeepSeek V3 API** — $0.30/M tokens, cheapest frontier-grade option
- **Claude Sonnet with prompt caching** — cost-effective for repeated-context workflows

## Linked Nodes

- implements: [[agent-system]]
- related_to: [[llm-routing-and-token-reduction]]
- related_to: [[task-system]]
