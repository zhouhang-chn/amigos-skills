# v0.2 Repository Gate — Action Plan

Story covered: **STORY-007**.

## Tasks

| Status | Task | Acceptance |
|---|---|---|
| [ ] | `src/amigos/gate.py`: path classification, story resolution, decision | Governed by default; resolution order honoured; ambiguity refuses |
| [ ] | `gate` config section and defaults | Exempt set configurable; absent config still fails closed |
| [ ] | `amigos gate` subcommand | `--staged`, `--changed-file`, `--story`, `--json`; exit 0/1/2 |
| [ ] | `amigos hooks install` | Writes `.git/hooks/pre-commit`; refuses to clobber a foreign hook |
| [ ] | `integrations/git/pre-commit` | Calls `amigos gate --staged` |
| [ ] | `integrations/claude-code/gate_hook.py` | Reads PreToolUse JSON, emits a deny decision with the reason |
| [ ] | Tests for every STORY-007 scenario | One test per scenario, named after it |
| [ ] | Install both hooks in this repository | The project is subject to its own gate |
| [ ] | Docs: component design, roadmap, README section 18 | Match the implementation |

## Verification

```bash
python -m pytest -q
amigos check STORY-007                      # exit 0

# governed change, ready story
AMIGOS_STORY=STORY-007 amigos gate --changed-file src/amigos/gate.py   # exit 0

# governed change, no story
AMIGOS_STORY= amigos gate --changed-file src/amigos/gate.py            # exit 1

# governed change, story not ready
AMIGOS_STORY=STORY-999 amigos gate --changed-file src/amigos/gate.py   # exit 1

# exempt change needs no story
AMIGOS_STORY= amigos gate --changed-file docs/README.md                # exit 0

# branch-name resolution, on this milestone's own branch
amigos gate --changed-file src/amigos/gate.py                          # exit 0

# the installed pre-commit hook actually fires
git commit --allow-empty -m probe                                      # runs the gate
```

## Risks

| Risk | Mitigation |
|---|---|
| A bug in the hook locks the repository out of editing | Tests pass before either hook is installed; the pre-commit hook is installed last; `.git/hooks/pre-commit` can be removed without a contract. |
| Fail-closed blocks routine metadata edits and provokes an escape hatch | The exempt set covers contracts, docs and root metadata — the work that makes a story ready. Anything beyond that is product feedback first, per README section 31. |
| The two adapters drift from the command | Neither adapter holds a rule; both call `amigos gate` and only translate its exit code. |
