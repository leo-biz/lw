---
title: Agent Orchestrator Landscape
node_type: reference
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - ai-agents
  - orchestration
  - coding-agents
  - ai-reviewed
created: 2026-06-04
updated: 2026-06-04
source:
  - https://www.reddit.com/r/ClaudeCode/comments/1psh80y/multi_agent_orchestration/
  - https://github.com/andyrewlee/awesome-agent-orchestrators
---

# Agent Orchestrator Landscape

## Purpose

Track existing open-source or common agent orchestration tools before Leo Life
builds its own session manager, worker adapter, or Slack control plane.

The current goal is practical: reduce bouncing between Codex, Claude Code,
Gemini, Aider, OpenCode, and other tools while preserving durable vault memory,
human approval, and safe publication boundaries.

## Current Decision

Evaluate existing orchestrators before building the local control plane from
scratch.

The first pass should focus on tools that can use subscription-backed local CLI
agents and preserve native auth, because Leo's pain is not only model routing;
it is managing many provider sessions and contexts.

## Source Leads

Primary discovery links from Leo:

- Reddit thread: [Multi agent orchestration](https://www.reddit.com/r/ClaudeCode/comments/1psh80y/multi_agent_orchestration/)
- Awesome list: [awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators)
- Leo-provided Google AI Mode chat history covering LiteLLM, 9Router, gateway
  chaining, Slack bus design, Groq/Cerebras/Gemini routing, BriefKit,
  Bernstein, RuFlo, BrowserBird, RelayPlane, Mattermost, and Open WebUI.

Useful takeaway from the Reddit thread:

```text
Task
-> Gemini spec
-> Claude Code plan/artifact
-> Gemini/Codex review loop
-> Claude Code implement
-> staged commit
-> Gemini final code/test review
```

This is close to Leo's desired flow, but it should be bounded by vault task
leases, file claims, context packets, and explicit approvals.

## Layers

Do not compare all tools as if they solve the same problem.

| Layer | Examples | What to evaluate |
|---|---|---|
| Control plane / workspace | CliDeck, Mux, Vibe Kanban, AgentPulse, Agentrove, Kandev | Session dashboard, worktrees, resume, logs, status, UX |
| Multi-agent orchestrator | Bernstein, Pied Piper, Composio Agent Orchestrator, kodo, orc, ORCH, Dex | Parallel/serial workflows, agent roles, approvals, PRs, audit trails |
| Chat / remote control | Bernstein, herdctl, OrbiqD BriefKit, multi_mcp, HeyAgent, takopi | Slack/Telegram/Discord/DM control, approvals, session commands |
| Coordination protocol / memory | guild, swarm-protocol, wit, gnap, shire | Claims, locks, handoffs, shared state, agent messaging |
| Worker | Codex CLI, Claude Code, Gemini CLI, Aider, OpenCode | Actual code editing and task execution |
| Router / gateway | LiteLLM, 9Router, OpenRouter, Claude Code Router | Model/provider/account routing, quotas, fallback |
| Brief/spec generator | BriefKit-style tools | Better task/context packet quality, not orchestration by itself |
| Browser worker | BrowserBird, browser-use style tools | Web task execution, QA, form flows, and browser automation |
| Chat/workspace surface | Mattermost, Open WebUI, Slack | Human interface, model chat, permissions, and pipelines; not necessarily coding-agent orchestration |

## Shortlist To Evaluate First

1. **Vibe Kanban** — mentioned for multi-agent worktree support and demos.
2. **CliDeck** — local dashboard/session UX candidate for multiple coding agents.
3. **Mux** — parallel agent development workspace with isolated workspaces.
4. **Bernstein** — CLI orchestrator for many coding agents, with chat control, worktrees, audit trails, PRs, approvals, and cost reporting claims.
5. **OrbiqD BriefKit** — MCP server that can drive local Claude/Codex/Gemini CLIs while preserving native auth/subscriptions.
6. **Pied Piper** — Claude Code subagent and Beads workflow approach; potentially useful for deterministic pipelines with approvals.
7. **multi_mcp** — mixes CLI-backed coding agents and API models in the same workflow.
8. **guild / swarm-protocol / wit** — coordination primitives worth comparing against the existing vault leases and file claims.

Also keep on the radar:

- AgentPulse
- Agentrove
- Kandev
- Composio Agent Orchestrator
- RuFlo
- Maestro
- claude-codex / claude-codex-gemini
- Every Code
- AxonFlow
- ORCH
- shire
- hcom
- kodo
- orc

Secondary candidates from later source passes:

- **BrowserBird** — browser automation worker, potentially Slack-accessible; useful for browser tasks but not core coding-session orchestration.
- **RelayPlane proxy** — routing/cost proxy in the LiteLLM/9Router layer; requires policy review if metadata leaves the local environment.
- **Mattermost** — possible self-hosted Slack alternative and MCP/agent control surface; bigger product decision than the current Slack pilot.
- **Open WebUI** — model/chat UI and pipeline host; useful as an AI home base, but not a coding-agent control plane by default.
- **BriefKit** — useful pattern for high-quality task/spec/context briefs; not the session manager itself.
- **Bernstein** — strong orchestrator candidate for CLI coding agents, chat control, worktrees, approvals, and audit trails.
- **RuFlo** — Claude-centered multi-agent/swarm candidate; evaluate carefully because broad swarm authority can create noise and safety risk.

## Evaluation Criteria

Use these questions before deciding to adopt, wrap, or build:

- Can it use subscription-backed Claude Code, Codex CLI, and Gemini CLI without API keys?
- Can it also support Aider and OpenCode?
- Does it support Slack, Discord, Telegram, or MCP control surfaces?
- Does it support same-session continuation and fresh-session starts?
- Does it isolate work via git worktrees or sandboxes?
- Does it preserve logs, transcripts, cost, and audit trails?
- Can it express serial and parallel pipelines with human approval gates?
- Can it integrate with Markdown task cards, leases, and file claims?
- Can it produce compact handoffs back to the vault?
- Does it require broad secrets, cloud sync, or risky permissions?
- Is it maintained enough for daily use?
- How much custom glue remains after adoption?

## Current Fit Hypothesis

The likely answer is not one tool replacing the vault.

More plausible:

```text
Existing orchestrator/workspace
-> manages CLI sessions, worktrees, and logs

Leo Life vault
-> remains durable memory, tasks, approvals, handoffs, and publication boundary

Small glue layer
-> maps tasks/context packets/approvals between both
```

Gateway tools such as LiteLLM, 9Router, RelayPlane, and OpenRouter should stay
below the orchestration layer. They can reduce model/provider/account friction,
but they do not decide task ownership, context packet contents, vault memory,
file claims, or Leo approval boundaries.

## 2026-06-04 Evaluation Pass

### Summary Decision

Adopt no full replacement yet. Pilot a small wrapper stack:

```text
Vibe Kanban or CliDeck
-> local session/workspace UX for multiple coding agents

OrbiqD BriefKit
-> cross-CLI review/spec loop using native Claude/Codex/Gemini auth

Leo Life vault
-> canonical tasks, claims, approvals, handoffs, logs, and publication boundary
```

Do not build the local session registry, Slack session commands, or first worker
adapter until those pilots prove what they cannot provide. The likely custom
work is an adapter/glue layer around vault task packets, not a replacement
orchestrator.

### Candidate Matrix

Score is practical fit for Leo's current problem, 0-3 per criterion:

- `subs` = subscription-backed local CLI support
- `chat` = Slack/chat/remote control
- `resume` = session continuation or handoff support
- `iso` = worktree/workspace isolation
- `audit` = logs, review, approval, or lineage
- `vault` = easy fit with Markdown tasks, leases, and file claims
- `risk` = safety/maintenance/permission posture, higher is safer

| Candidate       | Layer                                 | subs | chat | resume | iso | audit | vault | risk | Recommendation                                                                                                                                                                                                                                                                                                                            |
| --------------- | ------------------------------------- | ---: | ---: | -----: | --: | ----: | ----: | ---: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vibe Kanban     | control plane / workspace             |    3 |    1 |      2 |   3 |     2 |     2 |    2 | **Pilot** as the first visual task/workspace surface. Strong support for Claude Code, Codex, Gemini CLI, OpenCode, branches, terminals, preview, diff review, PRs, and merge. Missing piece is direct Slack control.                                                                                                                      |
| CliDeck         | control plane / remote control        |    3 |    2 |      3 |   1 |     1 |     2 |    2 | **Pilot** for "one browser/mobile window for all agent sessions." It directly targets Leo's switching pain and claims support for Claude Code, Codex, Gemini CLI, OpenCode, live status, resume, and phone control. Verify maturity and audit/log depth.                                                                                  |
| Mux             | control plane / workspace             |    1 |    0 |      2 |   3 |     1 |     1 |    2 | **Defer** unless Vibe Kanban fails. Strong isolated workspace UX, local/worktree/SSH modes, and agent-suite UI, but it appears to use its own agent loop and model/provider path rather than native subscription CLIs. AGPL licensing also needs consideration before wrapping.                                                           |
| Bernstein       | multi-agent orchestrator              |    3 |    2 |      2 |   3 |     3 |     1 |    1 | **Watch / later sandbox** for compliance-grade orchestration. Very strong claims: many CLI adapters, deterministic scheduling, git worktrees, signed audit chain, lineage, approvals, PRs, and Telegram/web/TUI control. Surface area and solo-maintained compliance/security complexity make it a second-phase pilot, not first install. |
| OrbiqD BriefKit | chat/remote control + brief/spec tool |    3 |    1 |      2 |   2 |     2 |     3 |    2 | **Pilot** as cross-CLI review/spec glue. It is a single Go CLI/MCP server that drives local `claude`, `codex`, and `gemini`, preserves native auth, logs executions, supports isolated copies, and maps cleanly to vault context packets. Not a full session dashboard.                                                                   |
| Pied Piper      | orchestrator / workflow               |    1 |    0 |      2 |   1 |     2 |     1 |    2 | **Defer** unless Claude-Code-subagent workflows become primary. Good Beads-backed task/workflow pattern with human approvals, but current practical support centers on Claude Code subagents rather than Codex/Gemini session management.                                                                                                 |
| multi_mcp       | router / model comparison             |    2 |    0 |      0 |   0 |     1 |     2 |    2 | **Wrap only for review loops**. Useful for multi-model compare/debate and CLI subprocess execution for Gemini/Codex/Claude, but it is not a control plane, claim system, or workspace manager.                                                                                                                                            |
| guild           | coordination protocol / memory        |    1 |    0 |      3 |   0 |     2 |     2 |    2 | **Study, do not adopt yet**. Its local SQLite project memory, MCP startup context, quest claims, journals, and handoff briefs overlap with the vault's current task/claim/memory system. It may inspire future simplification but should not replace Markdown canonical state.                                                            |
| swarm-protocol  | coordination protocol                 |    1 |    0 |      2 |   0 |     1 |     2 |    1 | **Defer**. Strong headless MCP coordination primitives for multi-human/multi-agent teams: intents, claims, heartbeats, conflict checks, auto-unblocking. Current alpha, trust-based identity, PostgreSQL requirement, and no Slack/UI make it less relevant for solo Leo workflow than existing vault leases.                             |
| wit             | coordination protocol                 |    1 |    0 |      1 |   0 |     1 |     1 |    2 | **Defer**. Symbol-level conflict detection through Tree-sitter is interesting for code repos, but it is single-machine, language-limited, advisory, Bun-based, and less useful for this Markdown vault/control-plane layer than file claims.                                                                                              |

### Tool-Specific Notes

**Vibe Kanban** should be the first workspace-dashboard test if Leo wants a
visual surface. It supports kanban issues, per-agent branch/terminal/dev-server
workspaces, inline diff review, app preview, PR creation, and a broad set of
coding agents including Claude Code, Codex, Gemini CLI, and OpenCode. It could
reshape `build-agent-session-registry` into a vault-to-Vibe task/context bridge.

#### Vibe Kanban Report-Only Pilot Review

Status on 2026-06-04: **defer live install unless Leo specifically wants a
local worktree/diff-review experiment. Do not treat it as the primary control
plane candidate.**

Current docs and README say Vibe Kanban runs with `npx vibe-kanban`, supports
Claude Code, Codex, Gemini CLI, GitHub Copilot, Amp, Cursor, OpenCode, Droid,
CCR, and Qwen Code, and uses each agent's existing installation/authentication.
Its core strength is workspace management: kanban issues, git worktrees,
generated branches, setup scripts, coding-agent sessions, code review, inline
comments, browser preview, PR creation, local merge, and cleanup.

The important 2026-06-04 finding is the sunset notice: bloop is shutting down,
Vibe Kanban will continue as open source/community maintained, remote services
will be removed, and local workspaces will continue to function. That means the
tool should be evaluated as a local workspace/diff-review shell, not a durable
team/cloud control plane.

Fit findings:

- It matches the worktree isolation and review surface better than CliDeck.
- It does not solve mobile/chat control as directly as CliDeck.
- It can use existing local CLI auth. Codex docs note default `~/.codex` and
  `CODEX_HOME` support; Claude, Gemini, and OpenCode docs each require the
  agent CLI to be installed/authenticated before launching Vibe Kanban.
- Workspaces create git worktrees under `.vibe-kanban-workspaces` by default
  and can run setup scripts automatically. That is useful but higher blast
  radius than CliDeck's session-only pilot.
- Remote access depends on Vibe Kanban cloud pairing/login. Given the sunset
  and remote-service removal, remote access should be considered out of scope.
- GitHub PR/merge integration is useful only after the GitHub publication
  boundary and secret/private-content scanner are settled.

Decision from report-only pass:

- Do not run it against this vault as the first live task. A real workspace test
  would create branches/worktrees and may start agents automatically.
- If Leo wants the live sandbox, use a disposable tiny Git repo, not the private
  vault, and verify only: install/start, local-only mode or sign-in skip,
  workspace directory, worktree creation, diff view, cleanup, and whether Codex
  can launch without extra config churn.
- Keep `build-agent-session-registry` blocked on Vibe only for the narrow
  question: whether an external workspace ID/worktree path is enough to map
  vault tasks to active workspaces. Do not wait on Vibe for chat/session
  control.

**CliDeck** may be the best match for the immediate "stop bouncing between
providers" pain. Its listed shape is a browser dashboard for multiple CLI agents
with live status, session resume, autopilot routing, and phone control. Its
pilot should verify whether it preserves native CLI sessions cleanly, records
enough audit trail, and can consume vault-generated context packets.

#### CliDeck Report-Only Pilot Review

Status on 2026-06-04: **desktop-local sandbox passed for Shell and Codex; keep
mobile remote untested until separately approved.**

Current docs say CliDeck is a local Node.js app with a browser UI at
`localhost:4000`, installable with `npm install -g clideck` or runnable once
with `npx clideck`. It requires Node 18+, supports macOS and Windows, and
defaults to binding `127.0.0.1`; `--host 0.0.0.0` is available for LAN/VPN but
should be avoided unless explicitly needed.

Fit findings:

- It uses real PTY sessions for `claude`, `codex`, `gemini`, OpenCode, shell,
  and custom terminal tools. It does not replace provider auth; agents run as
  normal local CLIs.
- Claude Code status/resume uses lifecycle hooks added to
  `~/.claude/settings.json` after one-time approval.
- Codex status/resume uses an `[otel]` section in `~/.codex/config.toml`
  pointing to `http://localhost:4000/v1/logs`, then `codex resume <sessionId>`.
- Gemini CLI status/resume uses a `telemetry` section in
  `~/.gemini/settings.json`, then `gemini --resume <sessionId>`.
- OpenCode uses a copied bridge plugin at
  `~/.config/opencode/plugins/clideck-bridge.js`, then
  `opencode --session <sessionId>`.
- CliDeck stores its own settings, saved sessions, transcripts, plugins, and
  autopilot logs under `~/.clideck/`.
- The mobile remote uses a Cloudflare relay for encrypted message transport.
  The docs claim the relay cannot decrypt content, but this still adds an
  external relay dependency and should be a separate approval gate.

Decision from report-only pass:

- Run the next sandbox as `npx clideck --port 4001` or `npm install -g clideck`
  followed by `clideck --port 4001`, with `127.0.0.1` binding only.
- Use a disposable shell session first, then one Codex session if Leo approves
  the `~/.codex/config.toml` telemetry change.
- Do not test mobile remote until the desktop-local session pilot succeeds.
- Keep custom Slack session commands deferred. If CliDeck works, Slack should
  initially link to or summarize CliDeck/session state instead of duplicating
  start/resume/clear behavior.

Live sandbox result:

- `npx clideck --host 127.0.0.1 --port 4001` started CliDeck v1.31.11
  successfully and seeded local plugins under `~/.clideck/plugins/`.
- Disposable Shell session launched, accepted terminal input, displayed output,
  and wrote a transcript under `~/.clideck/transcripts/`.
- Codex did not appear until added through Settings -> CLI Agents. After adding
  the Codex preset, CliDeck wrote `~/.clideck/config.json`.
- Codex setup patched `~/.codex/config.toml` with `hooks = true` and an `[otel]`
  exporter pointing at `http://localhost:4001`, and wrote two reviewed hooks to
  `~/.codex/hooks.json`.
- Codex hook review required explicit trust for `UserPromptSubmit` and `Stop`.
  Both hooks point to CliDeck's local `codex-hook.js` with port `4001`.
- A constrained Codex prompt returned `CLIDECK_CODEX_OK`; CliDeck showed the
  idle/status indicator and message preview in the sidebar.
- On `/quit`, CliDeck moved the Codex session to Previous Sessions with a
  captured resume token and Resume button.
- Server output confirmed `Telemetry: first event from Codex Desktop`,
  `captured session ID`, and `moved to resumable on exit`.

Important caveats:

- The initial default working directory was `/Users/sir/Documents`, which Codex
  treated as untrusted. Do not trust broad personal directories just for
  CliDeck. Configure a narrower default/project path before real use.
- Gemini CLI is installed but too old for CliDeck's requirement: local version
  `0.33.1`, warning requires `0.36.0+`.
- OpenCode is not installed locally.
- The Codex launcher still showed a stale `Needs re-patch` toast after patching,
  even though telemetry worked. Treat this as a CliDeck UI/state-refresh defect
  to monitor.
- The mobile remote was not tested. It remains a separate approval boundary
  because it uses an encrypted Cloudflare relay.

**OrbiqD BriefKit** is not a dashboard, but it is the best first candidate for
the Reddit-style deterministic review loop:

```text
vault task packet
-> Gemini spec/review
-> Claude or Codex implementation/review
-> staged diff
-> Gemini/Codex final review
-> vault handoff
```

Because it runs local `claude`, `codex`, and `gemini` CLIs through a CLI/MCP
server, it can preserve subscription auth and avoid a custom worker adapter for
simple review/spec tasks. Its logs and isolated workspace copies are enough for
a small safety pilot.

#### BriefKit Report-Only Pilot Review

Status on 2026-06-04: **best next live pilot after CliDeck; install/run still
requires approval because it adds local binaries/config under the user home.**

Current README says BriefKit runs local subscription-backed agent CLIs directly:
`claude`, `codex`, and `gemini`. It does not require API keys and does not
upload repository context. It ships as Go binaries: `briefkit-ctl`,
`briefkit-mcp`, and `briefkit-runner`, installable on macOS through Homebrew
with:

```bash
brew tap orbiqd/briefkit
brew install briefkit
```

Fit findings:

- It targets the exact worker-adapter layer that CliDeck does not solve:
  scripted calls such as `briefkit-ctl ask codex "..."` and cross-agent review
  loops.
- `briefkit-ctl setup` discovers local agent CLIs, writes agent configs, and can
  register the MCP server for supported runtimes.
- It can skip MCP registration with `--setup-agent-mcp=false`, which is the
  safer first sandbox because we only need CLI behavior.
- Default paths are under `~/.orbiqd/briefkit/`: agent configs, state, workspace
  runs, and runtime logs.
- The default no-workspace mode runs directly in the current working directory.
  Do not use that for the first vault test.
- `dir://` workspace mode copies a local directory into a fresh per-execution
  directory under `~/.orbiqd/briefkit/state/workspaces/runs/`; the agent works
  in the copy and the original is not modified.
- `git+https://` and `git+ssh://` workspace modes rely on existing Git
  credential helpers or SSH agent rather than new API keys.

Decision from report-only pass:

- Run a live sandbox only after approving Homebrew install and BriefKit setup.
- Use `briefkit-ctl setup --setup-agent-mcp=false` first, then
  `briefkit-ctl agent list`.
- Use a minimal generated task packet and `--workspace dir://<disposable repo>`
  so no private vault files are writable by the agent.
- Start with Codex only. Cross-agent review with Claude/Gemini is the second
  step if the first run behaves cleanly.
- If live sandbox passes, reshape `select-and-build-first-worker-adapter` into a
  thin wrapper around `briefkit-ctl ask` with explicit workspace, timeout, log
  capture, and vault handoff.

Live sandbox result:

- Homebrew installed BriefKit 0.9.1 from `orbiqd/briefkit`; Homebrew warned
  the tap is not trusted under upcoming tap-trust rules.
- `briefkit-ctl setup --setup-agent-mcp=false` found local `claude`, `codex`,
  and `gemini`, wrote agent YAML files under `~/.orbiqd/briefkit/agents`, and
  skipped MCP registration as intended.
- `briefkit-ctl agent list` returned three configured agents: `claude`,
  `codex`, and `gemini`.
- A disposable Git repo at `/tmp/briefkit-leolife-sandbox` was used with
  `--workspace dir:///tmp/briefkit-leolife-sandbox`. The original repo stayed
  clean.
- Codex run succeeded:
  execution `2f3eefc8-79d9-4a0e-b0ac-81cd9ede200d`, conversation
  `019e945a-b749-7bd0-84b6-2c02556139ad`, response:
  `BRIEFKIT_CODEX_OK` and `math.js exports add().`
- BriefKit wrote execution state under
  `~/.orbiqd/briefkit/state/executions/<execution-id>/` and runtime logs under
  `~/.orbiqd/briefkit/logs/runtime/codex/<execution-id>/`.
- The temporary copied workspace under `~/.orbiqd/briefkit/state/workspaces/runs`
  was removed after completion.

Live caveats:

- The Codex run used tools (`rg`) despite the prompt saying not to use tools.
  For a production adapter, treat BriefKit prompts as ordinary agent prompts
  and enforce write safety through workspace isolation, not natural-language
  instructions.
- Initial Codex run emitted OpenTelemetry connection errors because the earlier
  CliDeck pilot left shared Codex config exporting telemetry to stopped
  `localhost:4001`. This was cleaned up after the pilot by disabling shared
  Codex hooks/OTEL in `~/.codex/config.toml` and removing broad
  `/Users/sir/Documents` plus stale copied-workspace trust entries.
- Gemini execution failed because `/Users/sir/.gemini/settings.json` lacks an
  auth method and no Gemini auth environment variables were set.
- Claude execution started in a copied workspace but failed with
  `Credit balance is too low` because Claude Code inherited
  `ANTHROPIC_API_KEY` and selected API billing.
- Clean rerun after the CliDeck cleanup succeeded:
  execution `c1b8fb94-a42f-4152-8fae-f7705bbae40c`, conversation
  `019e945f-6bc2-70f2-bced-c0fa9e5540d4`, response
  `BRIEFKIT_CODEX_CLEAN_OK`; no OpenTelemetry connection errors remained.
- Claude session-auth rerun succeeded after removing Anthropic API env vars from
  the launched process:
  execution `1a0570a7-8715-4c1a-b6ad-d12dfc1e23e0`, conversation
  `1eebb0ef-dd6c-4f54-88f3-6fc253082181`, response
  `BRIEFKIT_CLAUDE_SESSION_OK`.
- Added local convenience wrappers:
  `/Users/sir/.local/bin/claude-session` for direct Claude session-auth runs and
  `/Users/sir/.local/bin/briefkit-claude-session` for BriefKit calls that should
  not use Anthropic API credits. Wrapper-backed BriefKit execution
  `73d80f43-379f-45d1-b211-64953958473b` returned
  `BRIEFKIT_CLAUDE_WRAPPER_OK`.

Decision from live pass:

- BriefKit is viable as a **Codex and Claude worker-adapter wrapper now**.
- BriefKit is not yet proven as a full Claude/Codex/Gemini cross-review loop on
  this machine because Gemini auth is not ready.
- Keep CliDeck telemetry disabled by default. Re-enable/repatch it only when
  actively running CliDeck, or isolate CliDeck and BriefKit with separate
  `CODEX_HOME` values before routine use.
- `select-and-build-first-worker-adapter` should be reshaped to wrap
  `briefkit-ctl ask codex --workspace dir://...` and
  `briefkit-claude-session ask --workspace dir://... claude ...` first, with
  Gemini expansion gated by local auth readiness.

**Bernstein** has the richest claimed feature set and should stay on the radar
for a later sandbox if the first pilots fail. It could obsolete much of a custom
orchestrator if its 40+ CLI adapters, worktree scheduling, approvals, lineage,
PR flow, and chat control work in practice. The caution is that this is also the
largest trust surface: audit keys, task server auth, agent cards, web UI/PWA,
many adapters, and compliance-oriented machinery.

**Mux** is strong as an isolated parallel-agent workspace, especially with local,
worktree, and SSH modes. It is less aligned with the immediate subscription-CLI
requirement because it presents its own agent loop and model/provider support.

**Pied Piper**, **guild**, **swarm-protocol**, and **wit** are more useful as
pattern libraries than immediate replacements. The vault already has task
leases, file claims, presence, activity logs, and handoff checkpoints; adopting
another coordination database before testing dashboards would add complexity.

### Impact On Blocked Tasks

`build-agent-session-registry` should be reshaped after Vibe Kanban and CliDeck
pilots. If either already tracks sessions, workspaces, status, resume handles,
and logs well enough, the registry becomes a mapping table from vault task IDs
to external session IDs instead of a full local session database.

`add-agent-session-slack-commands` should stay blocked. First prove whether
CliDeck mobile control, Vibe Kanban UI, or Bernstein/BriefKit command surfaces
cover enough remote control. Slack commands should target the winning surface,
not spawn a separate control plane prematurely.

`select-and-build-first-worker-adapter` should be reshaped around BriefKit
first. A minimal adapter can call `briefkit-ctl ask <agent>` with a generated
vault packet, capture logs, and write a handoff, which is narrower than building
native adapters for every provider CLI.

### Recommended Sandbox Order

1. Pilot CliDeck for local multi-agent session control and mobile/browser
   supervision.
2. Pilot Vibe Kanban for vault-backed tasks, workspaces, diff review, preview,
   PR, and merge.
3. Pilot BriefKit for cross-CLI review/spec loops using Claude/Codex/Gemini
   native auth.

Bernstein becomes a fourth pilot only if those three fail to provide enough
session orchestration, approvals, and logs.

## Compliance And Context Notes

From the Leo-provided Google AI Mode summary:

- Thread isolation is important. Multi-agent group chat can burn context and
  cause agents to respond to each other instead of the task. Prefer Slack
  threads, Matrix/Element threads, Open WebUI branches, or explicit context
  packets.
- Gateway chaining can have metadata mismatch failures. Any LiteLLM -> 9Router
  or 9Router -> LiteLLM pilot should test whether extra parameters are stripped
  or passed safely.
- Do not adopt tools primarily to bypass consumer subscription locks. If a tool
  uses browser/OAuth sessions, evaluate terms, stability, account risk, and
  whether the behavior is a supported private-use workflow before relying on it.
  This is an approval gate, not a default architecture.

Chat-surface candidates such as Open WebUI, Matrix/Element, Mattermost, and
Slack should be evaluated on control, history retention, thread isolation,
MCP/tool integration, and ease of mobile use. Replacing Slack is not required
unless the control/history benefits justify the product switch.

## Next Task

Run the focused pilots before implementing the self-built session manager,
Slack session commands, or first worker adapter:

- [[../../work/review/pilot-clideck-for-local-agent-control]]
- [[../../work/review/pilot-vibe-kanban-for-vault-backed-agent-workspaces]]
- [[../../work/review/pilot-briefkit-for-cross-cli-review-loop]]

Treat the local control plane as glue around the winning tool(s), not as a
from-scratch replacement unless the pilots fail.

## Linked Nodes

- related_to: [[slack-agent-command-center]]
- related_to: [[multi-agent-coordination]]
- related_to: [[llm-routing-and-token-reduction]]
- related_to: [[worker-capability-routing]]
