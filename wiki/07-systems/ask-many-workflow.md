---
title: Ask-Many Workflow
node_type: playbook
domain: systems
status: AI_REVIEWED
audience: private/internal
tags:
  - systems
  - ai-agents
  - multi-agent
  - coordination
  - ai-reviewed
created: 2026-06-09
updated: 2026-06-09
---

## Purpose

`ask_many.py` is a report-only multi-agent consultation tool. It generates
formatted prompt blocks — one per requested agent role — that the operator
pastes into each provider's session. After collecting responses, the operator
fills in a coordinator summary template.

No participants edit the vault, claim tasks, or write durable memory. The
script itself only generates prompts and saves the session log.

## Safety Contract

- **Report-only:** Participants must not edit any vault files, claim tasks, or
  write durable memory during an ask-many session.
- **Human in the loop:** The coordinator (Leo) collects responses manually and
  decides what, if anything, to promote to vault decisions or new tasks.
- **No cross-contamination:** Each role receives an independent prompt block
  with no awareness of what other roles will say. Synthesis happens only in the
  coordinator summary.
- **Scoped context only:** When `--task` is provided, the prompt block
  references that task ID but does not automatically load full vault context
  into the session — that remains the operator's judgment call.

## Known Roles

| Role    | Provider        |
|---------|-----------------|
| codex   | OpenAI Codex    |
| claude  | Anthropic Claude|
| gemini  | Google Gemini   |

Unknown roles produce a warning and are skipped. The session proceeds with
the remaining valid roles.

## CLI Usage

```bash
# Basic two-role consultation (saves to runs/ask-many/)
python3 scripts/ask_many.py \
  --prompt "Should we split the presence ledger into per-agent files?" \
  --roles codex,claude

# Three-role consultation scoped to a specific task
python3 scripts/ask_many.py \
  --prompt "What are the risks of removing the file-claim ledger?" \
  --roles codex,claude,gemini \
  --task task-2026-06-04-remove-file-claim-ledger

# Dry run: print prompts without saving a session file
python3 scripts/ask_many.py \
  --prompt "Is this design reversible?" \
  --roles codex,claude \
  --dry-run
```

### Arguments

| Flag         | Required | Description                                                  |
|--------------|----------|--------------------------------------------------------------|
| `--prompt`   | yes      | The question to put to each role.                            |
| `--roles`    | yes      | Comma-separated role list. Unknown roles are warned/skipped. |
| `--task`     | no       | Task ID to scope context (does not auto-load full context).  |
| `--dry-run`  | no       | Print without saving a session file.                         |

## Output

For each role the tool prints a labeled section header and a formatted prompt
block ready to paste:

```
============================================================
ROLE: CODEX
============================================================
You are Codex, an AI coding and systems agent.
You are operating in REPORT-ONLY mode: do not edit vault files, ...

---

**Question:**
Should we split the presence ledger into per-agent files?

---

Respond with your analysis. Do not edit any files or claim any tasks.
This is a report-only consultation.
```

A coordinator summary template follows all role sections:

```
============================================================
COORDINATOR SUMMARY TEMPLATE
============================================================
Fill this in after collecting all responses.

Agreements:
  -

Disagreements:
  -

Risks:
  -

Recommended Next Action:
  -
```

## Session Files

Unless `--dry-run` is passed, sessions are saved to:

```
runs/ask-many/YYYY-MM-DD-HH-MM-<slug>.md
```

The file contains:
- Session metadata (timestamp, prompt, roles, task ID if provided)
- Formatted prompt block for each role
- Blank response placeholder for each role
- Empty coordinator summary template

## Filling In the Summary

After pasting each prompt into its provider's session and collecting responses:

1. Open the saved session file in `runs/ask-many/`.
2. Paste each provider's response under the matching `### <role> Response` heading.
3. Fill in the **Coordinator Summary** section:
   - **Agreements:** points all roles converged on
   - **Disagreements:** points where roles diverged — these usually need Leo's
     judgment
   - **Risks:** concerns raised by any role
   - **Recommended Next Action:** what to do next, in one concrete step

## Promoting Findings

Ask-many sessions are ephemeral. To promote a finding:

- **Decision:** add an entry to the relevant wiki page or `log.md`.
- **New work:** create a task card in `work/inbox/` citing the ask-many session
  file path as the source.
- **Handoff:** reference the session file path in the next task's `## Activity`
  section.

Do not commit session files to Git unless the content is a durable reference
(e.g., the session resolved a significant architectural question).

## Linked Nodes

- implements: [[multi-agent-coordination]]
- related_to: [[task-system]]
- related_to: [[queue-worker-bootstrap]]
- related_to: [[agent-control-plane-operating-model]]
