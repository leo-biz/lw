---
title: Agent Control Plane Operating Model
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - slack
  - control-plane
  - ai-reviewed
created: 2026-06-04
updated: 2026-06-04
---

# Agent Control Plane Operating Model

## Purpose

Define the shared language and first build order for Leo's local agent control
plane.

The control plane should make it easy to chat with agents, start fresh work
sessions, continue useful context, save durable memory, and route cheap model
calls without turning Slack, provider chats, or API gateways into the source of
truth.

## Source Of Truth

```text
Slack = human-facing chat, commands, approvals, and alerts
vault = durable memory, tasks, decisions, packets, handoffs, and approval state
Git = change history and rollback
scripts = deterministic local automation
LiteLLM = API model gateway for cheap classification and summaries
BriefKit = first worker-adapter wrapper for local Codex and Claude CLI sessions
CliDeck = optional live session supervision and manual steering surface
workers = bounded execution sessions with tools
```

Do not let any one integration replace the vault. Provider sessions and Slack
threads are useful working surfaces; the vault remains canonical.

## Terms

**Model** is the inference engine that turns input into output, such as a Groq,
Cerebras, Gemini, OpenAI, Anthropic, or local model route. A model call alone
has no durable task ownership.

**Agent** is a role plus model or provider runtime plus instructions. Examples:
vault maintainer, coder, reviewer, researcher, dispatcher. An agent may run in
a provider chat, CLI session, API call, or deterministic script wrapper.

**Session** is one execution context with continuity: a Codex thread, Claude
Code session, BriefKit execution, CliDeck terminal session, Slack thread, or API
conversation. Sessions are disposable unless their results are written back to
the vault.

**Context** is what the current session can see right now. Context may include
the prompt, selected vault pages, task metadata, recent Activity, command
output, and a rolling summary. Context is not memory unless it is preserved.

**Memory** is durable, reviewed or reviewable state stored outside the current
session. In Leo Life, durable memory primarily means Markdown pages, task
Activity, logs, source evidence, commits, and explicit handoffs.

**Tool** is a bounded capability used by an agent or script: shell commands,
Git, Slack API, browser automation, LiteLLM calls, BriefKit execution, file
claims, task leases, or MCP connectors.

**Authority** is the permission boundary for an action. Reading, drafting,
editing, committing, sending Slack messages, installing software, spending
money, and publishing externally are different authority levels.

**Dispatcher** is the local process that receives Slack events or scheduled
triggers, classifies intent, creates or claims tasks, builds compact packets,
asks for approval, and hands work to scripts or worker adapters. The dispatcher
should not become the worker for judgment-heavy tasks.

**Worker** is a bounded execution session that receives a packet and performs a
specific job. Workers may read files, run tools, edit, test, commit, review, or
summarize depending on authority.

**Adapter** is the provider-specific wrapper that starts or continues a worker
and translates between vault packets and provider/session details. The first
adapter should wrap BriefKit for Codex and Claude session-backed calls.

**Orchestrator** coordinates multiple workers, workspaces, approvals, logs, and
handoffs. The vault plus dispatcher is the minimal orchestrator for now; tools
such as CliDeck, Vibe Kanban, BriefKit, and future candidates can provide
specific surfaces without replacing canonical vault state.

**LiteLLM** is the API gateway for low-cost model calls. Use it for model
aliases, budgets, fallback, provider normalization, and cheap routing jobs. Its
role should be tested broader than intent parsing: cheap models may handle more
triage, extraction, packet building, first-pass review, and draft synthesis than
the first architecture pass credits. Do not use LiteLLM as the authority layer
for vault edits or CLI worker execution.

## Session Semantics

### Same Session

Use the same session when the current context is still useful, the task is in
the same phase, and continuity is worth more than a fresh start.

Examples:

- continuing an active Codex or Claude implementation slice
- asking a follow-up question about a just-run command
- letting Leo manually steer a live CliDeck session

The same session should still checkpoint durable facts back to the vault before
context becomes large or brittle.

### New Session

Use a new session when starting a new task, changing roles, moving from
planning to implementation, switching providers, or after completing a coherent
phase.

New sessions should start from a compact task packet, not from an entire Slack
thread or vault dump.

### Clear Context

Clear context when the session is polluted, confused, too long, or carrying
irrelevant assumptions. Preserve useful state first through task Activity,
handoff notes, logs, or a packet.

Clearing context is not the same as deleting memory. It resets the working
window while durable memory remains available.

### Saved Memory

Save only durable value:

- decisions
- task state and Activity
- verification evidence
- source evidence
- reusable operating rules
- open questions
- handoff checkpoints

Do not save routine chatter, every intermediate thought, or provider-chat
transcripts unless the transcript itself is evidence.

## Work Modes

**Chat mode** answers, routes, drafts, and clarifies. It should default to
LiteLLM-backed cheap models for intent parsing and lightweight replies, then
escalate only when needed.

**Task mode** creates, claims, updates, or closes Markdown tasks. It must honor
task leases, file claims, approval boundaries, and Definition of Done evidence.

**Worker mode** starts a bounded Codex, Claude, or other provider session from a
compact packet. The worker should return status, output, transcript pointer,
session ID, residual risk, and next action.

**Review mode** asks another model, worker, or Leo to inspect a plan, diff,
decision, or result. Review may be report-only or may gate task closure.

## Subscription Workers And API Calls

Keep these paths separate.

```text
Cheap API path:
Slack or script
-> LiteLLM
-> Groq default
-> Cerebras fallback
-> approved complex model when explicitly needed
```

Use this path for intent classification, task lookup, queue ranking, compact
summaries, structured extraction, draft replies, report-only review, candidate
task packet construction, approval prompt drafting, and other reversible
judgment steps.

The operating bias should be:

```text
try cheap, reversible API judgment first
-> measure quality, latency, and failure mode
-> escalate to BriefKit worker only when tools, edits, long continuity, or
   higher reasoning quality are actually needed
```

This is an experimentation rule, not a permission expansion. Cheap model output
can recommend, summarize, classify, or draft; it still needs the dispatcher,
task system, or Leo to grant authority for consequential actions.

```text
Worker path:
vault task packet
-> BriefKit adapter
-> Codex CLI or Claude Code session auth
-> isolated dir:// workspace where appropriate
-> result and evidence written back to vault
```

Use this path for edits, tests, commits, repo inspection, longer reasoning,
tool use, and work that benefits from provider session continuity.

Groq and Cerebras save usage by handling high-volume lightweight calls.
BriefKit saves manual session management by launching local subscription-backed
workers. CliDeck saves attention by giving Leo a live supervision surface when
manual steering matters.

## Recommended Architecture

```text
Slack
-> local dispatcher
-> intent classification through LiteLLM when cheap judgment is enough
-> Markdown task adapter and task leases
-> compact context packet builder
-> approval gate when authority changes
-> deterministic script OR BriefKit worker adapter
-> task Activity, logs, handoff, and Git commit evidence
-> optional CliDeck supervision for live local sessions
```

The dispatcher decides whether a request is chat, task, worker, or review mode.
It should prefer the cheapest sufficient path while actively testing whether
cheap models are sufficient for more workflow steps than expected:

1. deterministic script when no model is needed
2. LiteLLM/Groq/Cerebras for lightweight judgment
3. LiteLLM/Groq/Cerebras report-only trials for reversible triage, extraction,
   review, and packet drafting
4. BriefKit/Codex or BriefKit/Claude for real worker execution
5. Leo approval before spending, publishing, installing, granting broad access,
   or allowing agents to create or steer other agents

## Minimum Viable Build Order

1. Keep the Slack-to-vault core as the stable command and approval loop.
2. Build the context packet builder so all routes start from bounded context.
3. Add small LiteLLM-backed report-only trials for packet drafting, task
   routing, and review so cheap-model upside is measured before worker
   escalation becomes the default.
4. Harden authority rules for Slack writes, vault edits, installs, spending,
   provider adapters, and external publication.
5. Unblock and build the first worker adapter around BriefKit for Codex and
   Claude session-backed calls.
6. Record worker execution IDs, provider, status, transcript/log pointers, and
   task links in a local session registry only after the adapter shape is known.
7. Add CliDeck supervision only where live inspection or resume materially
   helps; isolate its Codex telemetry config from routine BriefKit execution.
8. Add Gemini only after local Gemini CLI auth is ready.

## Approval Gates

Require Leo approval before:

- installing or updating third-party control-plane tools
- changing provider credentials, billing routes, or API spending limits
- giving Slack permission to post broadly, read DMs, read private channels, or
  act outside dispatcher-owned threads
- allowing a model-only route to edit vault files or run shell commands
- launching subscription-backed workers automatically
- granting worker access to secrets or broad filesystem scopes
- publishing or sending anything outside private/internal destinations
- marking pages `HUMAN_REVIEWED`
- allowing agents to create more agents or run open-ended autonomous loops

## Current Decisions

- LiteLLM remains the default gateway for API-style Slack routing and cheap
  model calls.
- Groq is the default lightweight Slack classifier route; Cerebras is the
  fallback; complex model routes require explicit reason and policy.
- Leo's review hunch on 2026-06-04: LiteLLM plus cheap models may have more
  practical upside than the first architecture credited. Treat that as a
  near-term experiment by measuring cheap model quality on reversible routing,
  extraction, packet drafting, and report-only review before escalating routine
  work to subscription-backed workers.
- BriefKit is viable now for Codex and Claude session-backed worker calls.
- Gemini worker expansion waits on local CLI auth.
- CliDeck is useful for live supervision and manual steering, but its Codex
  telemetry hooks should stay disabled during routine BriefKit runs or be
  isolated with separate `CODEX_HOME` values.
- The first worker adapter should wrap BriefKit rather than build separate
  direct Codex and Claude launchers first.

## Linked Nodes

- implements: [[slack-agent-command-center]]
- related_to: [[multi-agent-coordination]]
- related_to: [[llm-routing-and-token-reduction]]
- related_to: [[agent-orchestrator-landscape]]
- related_to: [[worker-capability-routing]]
- related_to: [[agent-role-registry]]
