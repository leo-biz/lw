# Leo Life Systems

Preview repository for Leo Life systems documentation and public-safe agent
tooling.

## Contents

- `wiki/07-systems/` — systems and agent-operations documentation.
- `scripts/` — sanitized task-lifecycle, queue selection, dependency graph,
  context packet, and publication-safety tooling.
- `scripts/tests/` — focused unit tests for the exported tooling.
- `docs/` — usage notes for the script package.
- `examples/` — example task files and input shapes.

## Script Requirements

Python 3.11+ with `PyYAML`:

```bash
pip install pyyaml
```

Run the exported script tests with:

```bash
python3 -m pytest scripts/tests/
```
