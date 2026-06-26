---
title: GitHub Publication Boundary
node_type: playbook
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: private/internal
tags:
  - systems
  - github
  - publishing
  - exports
  - safety
  - ai-reviewed
created: 2026-06-04
updated: 2026-06-07
---

# GitHub Publication Boundary

## Purpose

Define how Leo Life tooling and selected wiki-derived documentation can be
prepared for GitHub without publishing private vault memory, raw sources,
personal operational details, secrets, or client/public boundary mistakes.

GitHub should be a curated export or extracted codebase, not a direct mirror of
the vault.

## Hiring Signal Objective

The public GitHub surface should help future companies quickly understand that
Leo is actively building practical AI systems, not just collecting notes about
AI. It should show credible engineering judgment, shipped tooling, and clear
safety boundaries around private memory.

Target readers:

- recruiters looking for evidence of recent, hands-on AI work
- engineering managers evaluating system design, reliability, and taste
- AI tooling teams looking for agent coordination and workflow automation
  experience
- future collaborators deciding whether Leo can turn ambiguous workflow
  problems into usable infrastructure

The public narrative should be:

```text
Leo builds practical AI workflow systems:
agent coordination, Slack/control-plane operations, task automation,
LLM routing and cost control, review/lease protocols, and safe publication
boundaries for private knowledge systems.
```

This narrative should appear in the pinned repo descriptions, README opening
paragraphs, screenshots, diagrams, and project summaries. The signal is
strongest when a visitor can see both the product surface and the underlying
operating discipline: small scripts, tests, task lifecycle docs, architecture
notes, and visible commit cadence.

## Public Proof Points

Best-fit GitHub candidates for hiring signal:

- `dashboard/` as a public-facing operational surface when it can be shown
  without private data
- `scripts/` helpers for task leases, file claims, presence, context packets,
  validation, and publication safety scans after sanitization
- `wiki/07-systems/` docs rewritten into public-safe system design notes,
  especially task lifecycle, agent coordination, completion proof, Slack
  dispatcher, LLM routing, and GitHub publication safety
- generated diagrams that explain the agent workflow, queue selection,
  publication pipeline, and Slack/control-plane loop without showing private
  vault contents
- short READMEs that state the problem, show the workflow, list the core
  technical decisions, and link to tests or verification commands

Pinned GitHub repo/readme structure should favor:

- one polished private-preview-to-public systems repo over many thin repos
- a concise README with a real screenshot or diagram in the first viewport
- `docs/` pages organized by problem area rather than vault-internal location
- examples with fake paths, fake channel names, and example config
- visible tests, validators, and scanner output where practical
- project descriptions that mention AI agents, workflow automation, LLM routing,
  coordination protocols, and safety review in plain language
- regular commits that show active iteration without exposing raw private work

## Visible But Safe Criteria

Public material should be technical enough to be credible while still being
rewritten for the audience boundary.

Visible:

- reusable architecture and workflow patterns
- sanitized code, tests, fixtures, and example config
- system diagrams and screenshots with private values removed
- decision records that explain tradeoffs without personal or client context
- task and review protocols expressed as reusable engineering practices

Not visible:

- private vault memory, raw sources, inbox material, personal context, client
  details, provider account details, local absolute paths, secrets, tokens, or
  unreviewed claims presented as fact
- direct copies of `audience: private/internal` pages into public repos without
  rewrite and explicit review
- commit history or screenshots that reveal private operational details

Downstream audit/export/repo-structure tasks should use this test:

```text
Does this artifact help a hiring reader believe Leo can build useful AI
workflow infrastructure, and can it be published without leaking private memory
or operational secrets?
```

## Boundary

```text
public repo candidate
-> reusable code, tests, sanitized docs, config examples, README, license

private repo candidate
-> operational tooling, non-sensitive system docs, early previews, review drafts

do not publish by default
-> private/internal wiki memory, raw sources, inbox material, personal context,
   client-facing exports, tokens, local paths, provider secrets, unreviewed claims
```

Treat `audience: private/internal` as private by default. A page with private
audience may still inform a rewritten public doc, but it should not be copied
verbatim into a public repository without explicit review.

## Recommended Shape

Create or extract a separate GitHub repo for reusable agent/vault tooling:

```text
README.md
LICENSE
docs/
  task-system.md
  agent-presence.md
  slack-dispatcher.md
  session-manager-design.md
  llm-routing.md
examples/
  config/
src/ or scripts/
tests/
```

Use generic paths, generic user/channel names, and example config. Keep real
provider keys, local absolute paths, Slack workspace details, and private vault
content out of the repo.

## Export Pipeline

Prefer a generated export path:

```text
vault source page or script
-> sanitize/rewrite
-> exports/github-preview/
-> scanner
-> private GitHub preview
-> Leo review
-> public promotion only after explicit approval
```

The scanner should block likely leaks before any GitHub push:

- secrets or token-looking strings
- absolute local paths
- `raw/`, `private/`, inbox, and internal-only source references
- `audience: private/internal` copied verbatim into public docs
- client-facing or public export movement without explicit instruction
- personal names, workspace/channel IDs, and provider account details when not
  intentionally public
- unchecked `UNREVIEWED` or stale claims presented as settled documentation

## Publication Modes

| Mode | Use | Rule |
|---|---|---|
| Private preview repo | First GitHub destination for review | Allowed after scanner passes |
| Public repo | Reusable code and sanitized docs | Requires explicit Leo approval |
| Vault mirror | Whole vault or broad wiki copy | Do not do this |
| Generated docs export | Curated docs from rewritten sources | Preferred |
| Code extraction | Reusable scripts/tests/config examples | Preferred for tooling |

## Initial Candidate Scope

Good first candidates:

- task helper scripts and tests
- agent presence and file-claim helper patterns
- Slack dispatcher architecture after sanitization
- session manager design once implemented
- LiteLLM routing config examples without secrets
- docs explaining task lifecycle and completion proof patterns

Hold back by default:

- private memory pages
- raw inbox/source material
- personal workflows with sensitive context
- client/public exports
- local env files and real config
- provider usage/account details
- anything marked `HUMAN_REVIEWED` only if Leo explicitly approves public use

## Setup Sequence

1. Define and approve this publication boundary.
2. Audit scripts, docs, and wiki pages for publishable candidates.
3. Build a public-safe export pipeline.
4. Add a scanner for secrets, private audience, local paths, and raw/private
   references.
5. Extract reusable tooling into a repo-shaped staging directory.
6. Push a private GitHub preview.
7. Review rendered docs and diffs.
8. Promote selected material public only after explicit approval.

## Decisions (2026-06-05)

**Repo structure — single private repo first.**
One private GitHub repo for the full vault. Netlify connects to it directly —
deployed site URL is public, source stays private. This unblocks Netlify
immediately with zero additional complexity.

**Public mirror repos — deferred, not cancelled.**
When Leo is ready to make work publicly visible (hiring signal, open source),
a GitHub Action will fan out two public mirror repos automatically:
- `leolife-dashboard` — `dashboard/` + `netlify.toml`
- `leolife-systems` — `wiki/07-systems/` + `scripts/`

One push to the private vault triggers both mirrors. No restructuring needed.
Task: [[add-public-mirror-repos-for-dashboard-and-systems]]

**First repo visibility: private.**
The vault contains `audience: private/internal` identity and brand pages.
Private repo keeps all of that contained while still enabling Netlify deploys.

**Initial public candidate scope (when mirrors are activated):**
- `dashboard/` — static Netlify site, already clean
- `wiki/07-systems/` — systems docs, all `audience: private/internal` but
  no personal/sensitive content; suitable for public after Leo confirms
- `scripts/` — agent tooling; needs sanitization pass (remove local paths,
  example config only) before going public

**Scripts layout: stay under `scripts/` for now.**
Restructuring to a package layout is a separate task. Not worth the churn
until the control-plane work stabilises.

**License: pending Leo's decision.**
MIT is the default recommendation for open-source agent tooling. Leo to confirm
before public promotion. No license needed for the private repo phase.

**Origin framing: pending Leo's decision.**
Either "Leo Life agent tooling" (personal brand) or a standalone project name.
Decide when public mirror is ready to activate.

## Open Questions

- Which license? (MIT recommended — Leo to confirm before public promotion)
- Origin framing: Leo Life brand vs. standalone project name?

## Linked Nodes

- derived_from: [[vault-operating-model]]
- related_to: [[vault-operating-model]]
- related_to: [[slack-agent-command-center]]
- related_to: [[llm-routing-and-token-reduction]]
- related_to: [[agent-completion-proof-protocol]]
