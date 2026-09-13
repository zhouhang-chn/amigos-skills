# v0.5 `/implement` — Action Plan

Story: **STORY-006**. Branch: `story/STORY-006-implement-skill`.

## Tasks

- [x] 1. `amigos verify` in `src/amigos/verify.py`: re-derive readiness, load the
      `contract_hash` baseline from `dor.json`, compare each of the four input
      files, return a result carrying `ready`, per-file status and `verified`.
- [x] 2. Register `verify` in `src/amigos/cli.py`: story id, `--json`, the common
      `--root` / `--stories-dir`, and exit codes 0 / 1 / 2.
- [x] 3. `tests/test_verify.py`: match, differ, no baseline, not ready,
      structurally unusable, and a stale `ready: true` never yielding exit 0.
- [x] 4. `skills/implement/SKILL.md`: six phases, the seven bounds from
      `design.md`, and the prohibition on editing acceptance criteria.
- [x] 5. `.claude/skills/implement` symlink to `../../skills/implement`.
- [x] 6. `tests/test_skill_implement.py`: the skill held to the code, following
      the `tests/test_skill.py` pattern.
- [x] 7. `tests/test_cli.py`: `verify` registered, exit codes as documented.
- [x] 8. Closeout docs: `implementation-notes.md`, `docs/README.md` map row,
      `roadmaps.md` and `milestones.md` status, README section 0 status table.

## Acceptance criteria

Each task traces to a scenario in `.amigos/stories/STORY-006/acceptance.feature`:

| Task | Scenario |
|---|---|
| 1, 2, 3 | *A verification command decides whether the requirement was redefined* |
| 1, 3 | *A readiness verdict recorded in the story is not trusted on its own* |
| 4, 6 | *A story that is not ready gets no implementation* |
| 4, 6 | *A test for absent behaviour fails before the source changes* |
| 4, 6 | *A contract conflict stops the run instead of editing the contract* |
| 4, 6 | *An unsatisfied scenario is reported rather than made green* |
| 4, 6 | *A change no scenario requires is reported as scope expansion* |
| 4, 6 | *A Then no test can observe is named rather than dropped* |
| 4, 6 | *The run takes no privileged path around the gate* |
| all | *A ready contract reaches verified implementation* |

Two scenarios are decided by tests of a prompt's text rather than of behaviour.
They are listed in `implementation-notes.md` under the judgement method used, per
the contract's own rule about clauses no test can observe.

## Verification commands

```bash
python -m pytest -q                  # every test, including the new ones
amigos check STORY-006               # exit 0, ready
amigos verify STORY-006              # exit 0, contract unchanged since dor.json
amigos status                        # every story ready, exit 0
amigos gate --staged                 # this slice's own changes permitted
```

## Risks

| Risk | Mitigation |
|---|---|
| `verify` is written against a baseline an agent can rewrite by re-running `amigos check`. | Documented in `design.md` as the deliberate limit; closing it is v0.6's contract immutability. |
| The skill cannot be exercised in the session that writes it — skills are snapshotted at registration. | The milestone does not claim otherwise: v0.6's first story is the demonstration, and v0.5 stays open until then. |
| Writing `tests/*` and `skills/*` requires STORY-006 ready and resolvable. | Branch `story/STORY-006-implement-skill` names the story; `amigos check` passes. |
| Adding STORY-006 to `tests/test_dogfooding.py` edits a governed file the contract did not ask for. | Left alone. Reported as scope expansion in `implementation-notes.md` rather than done quietly. |
