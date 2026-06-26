---
title: Hermes Agent Runtime Evaluation
node_type: decision
domain: systems
status: AI_REVIEWED
audience: technical/internal
tags:
  - systems
  - ai-agents
  - slack
  - security
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
source: https://github.com/NousResearch/hermes-agent
---

# Hermes Agent Runtime Evaluation

## Decision

Test Hermes later as a sandboxed worker-runtime comparison. Do not adopt it as
the initial Slack dispatcher or durable system of record.

Proceed with the narrow Markdown-backed Slack pilot first. Revisit Hermes after
that pilot exposes which worker-runtime features are actually worth delegating.

## What Hermes Is

Hermes Agent is an MIT-licensed, self-hosted agent runtime maintained by Nous
Research. It is closer to Leo's Slack worker use case than Paperclip because it
already includes a multi-platform messaging gateway and an agent execution loop.

As of 2026-05-31, the official GitHub releases page lists `v0.14.0` dated
2026-05-16. The documented quick install is a shell installer from the official
repository. A future test should pin and review a release rather than piping the
latest installer directly into a long-lived production environment.

Its official documentation describes:

- Slack, Telegram, Discord, WhatsApp, Signal, email, and other messaging adapters
- Slack Socket Mode with no public HTTP endpoint required
- model selection and switching across hosted and local providers
- curated persistent memory, session search, and optional memory-provider plugins
- reusable procedural skills that can be created and improved over time
- cron scheduling with fresh sessions and no-agent script mode
- isolated subagent delegation with focused `goal` and `context` packets
- local, Docker, SSH, Singularity, Modal, and Daytona terminal backends

## Fit With The Slack Pilot

Hermes could accelerate a future iteration by supplying a ready-made Slack bot,
thread sessions, per-channel prompts, channel skill bindings, model switching,
cron delivery, and bounded parallel delegation.

It should not replace the current baseline:

| Hermes | Leo Life Wiki Baseline |
|---|---|
| Hermes sessions and memory | Markdown files remain durable memory |
| built-in cron | deterministic scripts remain token-free by default |
| command approval prompts | durable business approvals remain vault task state |
| subagent summaries | vault work packets remain explicit and auditable |
| Slack gateway | Slack remains a communication surface, not the system of record |

The Slack adapter requests broader read scopes when full Hermes chat behavior is
enabled. A narrow custom dispatcher can start with a smaller surface and add
capabilities only when required.

## Operational Tradeoffs

Hermes is self-hosted, but inference and optional tool services still have
costs. Operators can bring provider keys, use local OpenAI-compatible endpoints,
or use the Nous Portal subscription. Scheduled agent runs use the configured
model; no-agent cron mode can run scripts without LLM usage.

Adopting Hermes also creates an update and configuration surface: gateway
tokens, model credentials, memory files, skills, allowlists, terminal backends,
and optional MCP servers must be maintained. That is reasonable for a focused
worker-runtime experiment but premature as the foundation of the first Slack
pilot.

## Security Review

Hermes documents a defense-in-depth model with user allowlists, DM pairing,
dangerous-command approval prompts, MCP environment filtering, prompt-injection
scanning, cross-session isolation, and optional container backends.

Its official security policy is explicit: nothing inside the agent process is a
containment boundary. Approval gates, output redaction, pattern scanners, and
tool allowlists reduce risk but do not replace isolation. Authorized users
inside one adapter are equally trusted; capability separation requires separate
Hermes instances with separate allowlists.

For an eventual Slack test, use Socket Mode, explicit user and channel
allowlists, a non-root process, a Docker-backed terminal, synthetic data, and a
non-sensitive working directory. Do not use production credentials or private
vault data during the comparison.

## Smallest Safe Future Test

1. Install Hermes in a disposable environment from a reviewed release.
2. Use a dedicated test Slack app and workspace or isolated test channel.
3. Configure Socket Mode, explicit allowed users, explicit allowed channels, and DM pairing.
4. Set `terminal.backend: docker` with no forwarded environment secrets.
5. Point `MESSAGING_CWD` at a disposable synthetic workspace.
6. Test one Slack thread, one model switch, one cron delivery, one dangerous-command denial, and one bounded delegated research task.
7. Compare context cost, auditability, and operator friction against the narrow Markdown-backed dispatcher.
8. Decide whether Hermes should remain separate, become an optional worker adapter, or be deferred.

## Primary Sources

- official repository: https://github.com/NousResearch/hermes-agent
- official releases: https://github.com/NousResearch/hermes-agent/releases
- official documentation: https://hermes-agent.nousresearch.com/docs/
- Slack gateway: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/slack
- security model: https://hermes-agent.nousresearch.com/docs/user-guide/security/
- security policy: https://github.com/NousResearch/hermes-agent/security
- persistent memory: https://hermes-agent.nousresearch.com/docs/user-guide/features/memory/
- cron scheduling: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron/
- subagent delegation: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation
- model providers: https://hermes-agent.nousresearch.com/docs/integrations/providers

## Linked Nodes

- derived_from: [[../05-learning/transcript-reviews/ai-news-2026-05-29-agent-studio-tools]]
- related_to: [[slack-agent-command-center]]
- related_to: [[multi-agent-coordination]]
- related_to: [[../../work/done/evaluate-hermes-for-agent-dispatch]]
