---
title: sqz Context Compression
node_type: reference
domain: systems
status: AI_REVIEWED
reviewed_by:
reviewed_date:
audience: technical/internal
tags:
  - systems
  - ai-agents
  - automation
  - context-compression
  - ai-reviewed
created: 2026-05-21
updated: 2026-05-31
---

# sqz Context Compression

## Summary

`sqz` is a Rust-based LLM context compression tool active in this vault via MCP.
It reduces token waste across file reads, command output, diffs, logs, and
context handoffs. The MCP server exposes six tools and injects session env vars.

## MCP Tools

### File and Search Tools

| Tool            | Use for                                                                                      |
| --------------- | -------------------------------------------------------------------------------------------- |
| `sqz_read_file` | Any file >2KB or likely to be re-read. Dedup cache returns a 13-token `§ref:HASH§` on repeat reads. |
| `sqz_list_dir`  | Directory listings. Skips bulk dirs automatically.                                           |
| `sqz_grep`      | Grep returning many lines. Output is 40–70% smaller than raw grep.                           |

Prefer these over `Read`, `ls`, and `Bash grep` for vault work. Use the built-in
`Read` tool only when the Edit tool requires it (Edit needs a prior Read call,
not a sqz read) — and when you do, read the bare minimum: target the exact
lines you need to match for the edit, not the whole file.

```python
# You already understand the file from sqz — now satisfy Edit's prerequisite
Read(file_path="scripts/example.py", offset=1, limit=3)   # just the docstring line
Edit(...)   # now allowed
```

### Text Pipeline Tools

| Tool | Use for |
|---|---|
| `compress` | Pipe large Bash output through before it hits context. Call after any command that returns >1KB. |
| `expand` | Resolve a `§ref:HASH§` dedup token back to full content. Pass just the hex prefix. |
| `passthrough` | Get byte-exact output when you cannot parse a compressed form. |

**`compress` pattern — use it on large command output:**

```python
# run the command via Bash, capture output, then compress before it lands in context
output = bash("python3 scripts/wiki_health_check.py")
mcp__sqz__compress(text=output)   # → compressed version enters context
```

**`expand` pattern — recover a deduplicated read:**

```python
# sqz_read_file returns: §ref:06aa5df4§  (content seen earlier this session)
mcp__sqz__expand(prefix="06aa5df4")   # → full original content
```

## Session Env Vars

sqz injects these into the agent environment:

```bash
__SQZ_CMD=claude --resume   # the resume command for the current session
```

Combined with `CLAUDE_CODE_SESSION_ID` (Claude Code) or `CODEX_THREAD_ID`
(Codex Desktop), an agent can always recover its own resume key without
hardcoding it. See [[agent-presence-ledger#Provider Session IDs]].

## Usage Rules

Use `sqz_read_file`, `sqz_grep`, and `sqz_list_dir` by default for vault work.
Use `compress` on any Bash output larger than ~1KB before it enters context.
Use `expand` when a `§ref:HASH§` token appears and full content is needed.

Do not use lossy compression as the sole read path when exact wording, raw
evidence, pricing, public copy, secrets, or safety-critical details matter.
Direct-read those passages with the built-in `Read` tool.

Fall back to targeted direct reads and state briefly if sqz is unavailable.

## Risks

- Compression can hide important nuance if applied too aggressively.
- Decision pages, pricing, public-facing copy, and source evidence need direct reads.
- The dedup cache is session-scoped — a `§ref:HASH§` token from a prior session cannot be expanded in a new one.

## Linked Nodes

- related_to: [[agent-system]]
- related_to: [[learning-to-application-loop]]
- related_to: [[wiki-operating-rules]]
- derived_from: [[agent-system]]
- related_to: [[queue-worker-bootstrap]]
