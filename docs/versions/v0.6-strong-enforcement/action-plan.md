# v0.6 Strong Self-Hosting Enforcement — Action Plan

## Milestone sequence

- [x] 1. **STORY-009** — contract immutability: the baseline moves to git history.
- [x] 2. **STORY-010** — the gate refuses a contract edit while a story is ready.
- [ ] 3. Enforcement outside the session: CI re-running the gate over a push range.
- [ ] 4. Governed writes made through `Bash`.
- [ ] 5. Blocked stories, and a hand-edited `state.json`.

Tasks 1 and 2 are contracted and built. Each later task needs its own `/amigos`
run before it has one, and the order is not arbitrary: every later protection
assumes a baseline that cannot be moved from inside the session, which is task 1.

## STORY-009

Branch: `story/STORY-009-contract-immutability`.

This story is built by running `/implement` against its contract. That is not an
acceptance criterion — nothing observable distinguishes a run record written by
the skill from one written by hand — but it is the milestone obligation
`milestones.md` and v0.5's implementation notes both record, and it is how v0.5
gets the demonstration it has been held open for.

The tasks below are therefore **predictions, not instructions**. `/implement`
derives its own work from the nine scenarios in `acceptance.feature`; if what it
does diverges from this list, the list is what was wrong.

- [x] 1. Baseline derivation in `src/amigos/verify.py`: resolve the work-tree
      root, find `C0`, find `I0` in `C0..HEAD` using `gate.classify()`, return
      `I0^` or HEAD.
- [x] 2. Comparison against the baseline through git, so repository content
      filters are applied rather than bypassed.
- [x] 3. Report the baseline revision in the command's output and in `--json`.
- [x] 4. Map the new failure modes onto exit code 2, distinctly from 1.
- [x] 5. Git-backed fixtures in `tests/conftest.py` able to build the
      three-commit shape: contract, governed change, contract edit.
- [x] 6. `tests/test_verify.py` for the nine scenarios.
- [x] 7. Closeout: `implementation-notes.md`, `docs/component-design/execution.md`,
      `milestones.md`, `roadmaps.md`.

## Acceptance criteria

Each task traces to a scenario in `.amigos/stories/STORY-009/acceptance.feature`:

| Task | Scenario |
|---|---|
| 1 | *The baseline is the parent of the first governed change* |
| 1, 2, 3 | *An unchanged contract verifies against its committed baseline* |
| 1, 6 | *Re-running the readiness check does not launder a contract edit* |
| 1, 6 | *A contract edit committed during implementation does not become the baseline* |
| 4 | *A contract that was never committed is unanswerable* |
| 1, 6 | *A readiness verdict written by hand produces no pass* |
| 1, 6 | *A change outside the story directory is not a contract change* |
| 1, 6 | *A contract rewritten through contract_change stays verifiable* |
| 2 | *A configured content filter does not produce a difference* |

## Verification commands

```bash
python -m pytest -q                  # every test, including the new ones
amigos check STORY-009               # exit 0, ready
amigos verify STORY-009              # exit 0, contract unchanged since the baseline
amigos status                        # every story ready, exit 0
amigos gate --staged                 # this slice's own changes permitted
```

## Risks

| Risk | Mitigation |
|---|---|
| The contract must be committed before implementation starts, or the baseline cannot be derived. | The contract lands in its own commit, before the implementation branch carries any governed change. This is also what the first scenario tests. |
| Every current `verify` test runs on a non-git fixture, so the fixture work is larger than the feature. | Named as task 5 and carried in `constraints.md` under Dependencies, so it is planned rather than discovered. |
| `/implement`'s Phase 0 runs `amigos check`, which rewrites `dor.json`. | Harmless once the baseline is git: the rewritten field is no longer the authority. It still dirties the tree, which is gap 10 and not this story. |
| The baseline is derived from history reachable from HEAD, so a rebase moves it. | Recorded in `design.md` and in `open-questions.md` as a deliberate limit, not a defect. |
| `/implement` is being exercised for the first time and may stop on a contract conflict. | That is a working outcome, not a failed run. The contract is left byte-identical, the conflict is reported, and a human decides. |


## STORY-010

Branch: `story/STORY-010-gate-refuses-contract-edit`.

Built by running `/implement` against the contract committed at `a39d448`, which
this session drafted through `/amigos` but did not author by hand.

- [x] 1. `gate.contract_file()`: map a changed path to `(story_id, file)` through
      `config.stories_dir`, never through the literal prefix `.amigos/stories/`.
- [x] 2. `gate._ready_before_change()`: the working tree at edit time, `HEAD` at
      commit time, failing open on anything that cannot be evaluated.
- [x] 3. `gate._ready_at_head()`: the four contract inputs from `HEAD`, the live
      `state.json` beside them, evaluated through an overridden `stories_dir`.
- [x] 4. `gate.decide()` gains the `staged` parameter and asks the new question
      before the exempt-set early return.
- [x] 5. `Decision.frozen`, additive in `--json`; existing keys keep their meaning.
- [x] 6. `gate.staged_paths()`: `--diff-filter=ACMRT` gains `D`.
- [x] 7. `cli._gate()`: a frozen-contract refusal names the reopening route
      instead of `Make the story ready`.
- [x] 8. `tests/test_gate_contract_freeze.py`, one test per scenario.
- [x] 9. Closeout: `gate.md`, `design.md`, this plan, `implementation-notes.md`.

### Acceptance criteria

| Task | Scenario |
|---|---|
| 1, 2, 4 | *An edit to a ready story's acceptance criteria is refused* |
| 2, 4 | *Declaring a withholding state reopens the contract* |
| 2, 3 | *An edit that would leave the story unready is refused all the same* |
| 3 | *The commit that first records a ready contract is permitted* |
| 2 | *A story that is not ready keeps an editable contract* |
| 1 | *Only the contract inputs are frozen, not the records beside them* |
| 1, 4 | *The refusal follows the story the path names, not the active one* |
| 2 | *A story whose contract cannot be evaluated stays editable* |
| 6 | *A staged deletion of a ready story's contract file is refused* |
| 2 | *Scaffolding a new story is permitted while another story is ready* |

### Verification commands

```bash
python -m pytest -q                  # 343 passed
amigos check STORY-010               # exit 0, ready
amigos verify STORY-010              # exit 0, baseline a39d44861080
amigos status                        # nine stories ready, exit 0
amigos gate --staged                 # this slice's own changes permitted
```

### Risks

| Risk | Mitigation |
|---|---|
| The rule takes effect inside the session that writes it, so a too-broad rule locks the session out of the files it needs to fix it. | Nothing outside `config.stories_dir` can be refused by this rule, stated as a constraint before implementation. |
| A commit-time refusal deadlocks this repository's own contract commits. | Readiness at commit time comes from `HEAD`, so an uncommitted contract has nothing to protect. Tested as its own scenario. |
| Failing open makes a corrupt `state.json` an unlock. | Stated rather than hidden. A hand-written `contract_change` is an equally cheap unlock and is gap 8, task 5. |
| Adding `D` to the staged collector changes decisions beyond this story. | Intended: a staged deletion of a governed path now needs a ready story, which is what fail-closed already implies. `working_tree_paths()` is left alone and recorded. |
