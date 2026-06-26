---
title: Paperclip Agent Orchestration Evaluation
node_type: decision
domain: systems
status: AI_REVIEWED
audience: technical/internal
tags:
  - systems
  - ai-agents
  - orchestration
  - security
  - ai-reviewed
created: 2026-05-31
updated: 2026-05-31
source: https://github.com/paperclipai/paperclip
---

# Paperclip Agent Orchestration Evaluation

## Decision

Defer Paperclip adoption. Proceed with the narrow Markdown-backed Slack pilot.

Revisit Paperclip only after the custom pilot reveals coordination friction that
the current file-native workflow does not handle well.

## What Paperclip Is

Paperclip is a self-hosted Node.js server and React UI for orchestrating teams of
AI agents. It is a control plane, not an agent framework or Slack bridge.

Its official repository documents:

- goals, org charts, issues, comments, blockers, and approval workflows
- scheduled heartbeats and event-triggered agent wakeups
- budgets, cost tracking, audit activity, and multi-company isolation
- adapters for Claude Code, Codex, Cursor, local processes, and HTTP services
- local encrypted secret storage and authenticated deployment modes

## Fit With Leo Life Wiki

Paperclip overlaps with several workflows already implemented in the vault:

| Paperclip | Current Vault Baseline |
|---|---|
| ticket system and blockers | Markdown tasks under `work/` |
| heartbeats and routines | deterministic scripts and `launchd` |
| agent activity | task leases and append-only activity |
| operator dashboard | Obsidian Task Base and local read-only dashboard |
| approvals and audit trail | Markdown task state and durable decisions |

Paperclip adds a richer multi-agent control plane. That may become useful when
the number of concurrent agents, scheduled workers, approvals, and budgets makes
the Markdown-first baseline cumbersome. It is premature for the first Slack
dispatcher pilot.

## Security Review

The official repository is MIT-licensed and actively maintained. As of
2026-05-31, GitHub lists release `v2026.529.0` dated 2026-05-30.

The project has also published recent security advisories, including previously
affected versions with unauthenticated remote-code execution, cross-tenant API
key issues, command injection, and unsafe skill behavior. Current patched
versions are newer than the affected releases, but the advisory history makes a
network-exposed or live-secret pilot inappropriate without a separate security
review.

The default quickstart uses trusted local loopback mode. Authenticated, LAN, and
tailnet deployments require additional care. Local encrypted secrets use a
master key stored under the Paperclip instance directory. Telemetry is enabled
by default but can be disabled.

## Smallest Safe Future Pilot

If Paperclip is revisited:

1. Use the latest reviewed release in trusted local loopback mode only.
2. Use a disposable test workspace and synthetic tasks.
3. Do not provide production credentials, private vault data, or live client data.
4. Disable telemetry with `PAPERCLIP_TELEMETRY_DISABLED=1`.
5. Review installed adapters, plugins, and skills before enabling them.
6. Test one Codex worker, one bounded task, one approval, and one budget limit.
7. Reassess before allowing LAN, tailnet, or internet exposure.

## Primary Sources

- official repository: https://github.com/paperclipai/paperclip
- official documentation: https://docs.paperclip.ing/
- adapter overview: https://github.com/paperclipai/paperclip/blob/master/docs/adapters/overview.md
- development and secret handling: https://github.com/paperclipai/paperclip/blob/master/doc/DEVELOPING.md
- database and local encrypted secrets: https://github.com/paperclipai/paperclip/blob/master/doc/DATABASE.md
- official security advisories: https://github.com/paperclipai/paperclip/security

## Linked Nodes

- derived_from: [[../05-learning/transcript-reviews/youtube-agent-wiki-and-orchestration-patterns]]
- related_to: [[slack-agent-command-center]]
- related_to: [[multi-agent-coordination]]
- related_to: [[../../work/done/evaluate-paperclip-agent-orchestration]]
