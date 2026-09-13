# Project Overview

## What this is

`amigos-skills` turns the Three Amigos practice — Product, Development and QA
alignment — into an executable pre-development gate for coding agents. A ticket
becomes a repository-local acceptance contract under `.amigos/`, and that
contract, not the chat history, is the authoritative specification for every
agent that follows.

The controlling principle, from README section 35:

> Models can propose readiness. Deterministic rules control the gate.

## Layers

```text
 contract protocol   .amigos/            platform-independent, hand-editable
         |
 deterministic core  src/amigos/         parses and judges the contract
         |
 repository gate     hooks, CI           makes bypassing the contract hard
         |
 agent orchestration skills/, agents/    produces contracts and implements them
```

Lower layers must be trustworthy before higher ones are worth building. That
ordering is why the deterministic core ships before `/amigos`, and why
enforcement ships before agent orchestration. See [roadmaps.md](roadmaps.md).

## Layout

| Path | Contents |
|---|---|
| `.amigos/` | The protocol: repository config and one directory per story. |
| `src/amigos/` | The deterministic core. Standard library only. |
| `scripts/` | Thin wrappers so each capability has a documented script entry point. |
| `schemas/` | JSON Schema for the two machine-readable contract files. |
| `templates/` | The scaffolding `amigos create` writes. |
| `tests/` | Unit tests plus a fixture corpus of deliberately broken stories. |
| `docs/` | This documentation. |
| `.claude-plugin/` | Claude Code plugin manifest. |

`skills/` and `agents/` arrive with `/amigos` in a later milestone; the plugin
manifest declares them at that point, not before.

## Runtime

Python 3.11 or newer, no third-party runtime dependencies. The gate has to run
inside any repository without an install step, so even JSON Schema validation is
implemented in-tree (`src/amigos/jsonschema.py`) against the narrow keyword set
this project's schemas use.

`pytest` is the only development dependency.

## Current state

Milestone v0.1 is implemented: the contract format, the deterministic validator,
the acceptance linter and story scaffolding. The project's own three stories are
contracts under `.amigos/stories/` and are held to the same gate by
`tests/test_dogfooding.py`.
