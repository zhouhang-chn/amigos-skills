# Integrations

The contract under `.amigos/` is the protocol. Everything here is an adapter
that lets a particular host consult it. No adapter holds a rule: each collects
changed paths, calls `amigos gate`, and translates the exit code.

| Path | Host | Wiring |
|---|---|---|
| `claude-code/gate_hook.py` | Claude Code | A `PreToolUse` hook on `Edit`, `Write` and `NotebookEdit`. See the docstring for the `.claude/settings.json` block. |
| `git/pre-commit` | git | `amigos hooks install` writes this into `.git/hooks/pre-commit`. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | permitted |
| 1 | refused |
| 2 | the gate could not run |

Code 2 is kept distinct because "you may not do this" and "I could not tell"
need different responses from whoever is reading.
