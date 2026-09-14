# v0.6 Strong Self-Hosting Enforcement — Action Plan

## Milestone sequence

- [x] 1. **STORY-009** — contract immutability: the baseline moves to git history.
- [x] 2. **STORY-010** — the gate refuses a contract edit while a story is ready.
- [ ] 3. Enforcement outside the session: CI re-running the gate over a push range.
- [ ] 4. Governed writes made through `Bash`.
- [x] 5. **STORY-011** — contract state evidence, and blocked stories.

Tasks 1, 2 and 5 are contracted and built. Task 5 was taken ahead of 3 and 4
because STORY-010 made it load-bearing: the freeze it shipped reads its unlock
from `state.json`, and nothing verified that file. Each later task needs its own `/amigos`
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


## STORY-011

Branch: `story/STORY-011-contract-state-evidence`.

Built by running `/implement` against the contract committed at `c35704b`.
As with STORY-009 and STORY-010 the tasks below are **predictions, not
instructions**: the skill derives its work from the twelve scenarios in
`acceptance.feature`, and where the two diverge the list is what was wrong.

- [x] 1. `story_file()` in `src/amigos/gate.py`, with `contract_file()` and a new
      `lifecycle_file()` derived from it, so a path is named by location and not
      by string prefix.
- [x] 2. `LifecycleReport`, and the three checks: declaration recorded, timestamp
      recorded, committed history still a prefix.
- [x] 3. `lifecycle_report()` reading the record as the change would leave it —
      the index under `--staged`, the working tree otherwise.
- [x] 4. `lifecycle_refusals()`, implicating a story strictly for its contract or
      as the resolved story, leniently for its own `state.json`.
- [x] 5. The question asked in `decide()` *before* the contract freeze.
- [x] 6. `amigos state <ID>` with no `--set` reports the record: 0 consistent,
      1 inconsistent, 2 could not read.
- [x] 7. A blocked story's refusal names the derived state, a failed check, and
      the amigos skill.
- [x] 8. `tests/test_gate_lifecycle.py`, one test per scenario.
- [x] 9. Closeout: `gate.md`, `design.md`, this plan, `implementation-notes.md`.

## Acceptance criteria

Each task traces to a scenario in `.amigos/stories/STORY-011/acceptance.feature`:

| Task | Scenario |
|---|---|
| 2, 5 | *A declared state the history does not record is refused* |
| 2, 3 | *A history entry removed after it was committed is refused* |
| 7 | *A governed change under a blocked story is refused with the route out* |
| 2, 6 | *A reopening recorded through the state command is permitted* |
| 5 | *Declaring contract_change still reopens a frozen contract* |
| 3, 4 | *The commit that would launder a rewritten history is refused* |
| 1, 4 | *A write to the story's own state.json is permitted while the record is inconsistent* |
| 2, 5 | *A state.json that cannot be parsed is refused rather than permitted* |
| 2, 6 | *A state.json that was never committed is not reported as inconsistent* |
| 7 | *No declarable state makes a blocked story permit a governed change* |
| 2, 6 | *Every story in this repository passes the consistency rule* |
| 6 | *The report writes nothing* |

## Verification commands

```bash
python -m pytest -q                  # every test, including the new ones
amigos check STORY-011               # exit 0, ready
amigos verify STORY-011              # exit 0, contract unchanged since the baseline
amigos status                        # every story ready, exit 0
amigos gate --staged                 # this slice's own changes permitted
```

## Risks

| Risk | Mitigation |
|---|---|
| A tamper check routed through readiness releases the contract freeze instead of holding it, because the freeze fails open. | The refusal is a gate decision and never a readiness verdict. Named as an invariant in `constraints.md` and held by the scenario *Declaring contract_change still reopens a frozen contract*. |
| A corrupt `state.json` cannot be repaired by `amigos state`, which parses before writing, so refusing the hand repair deadlocks the repository. | A write to a story's own `state.json` stays permitted. Held by its own scenario. |
| The new question fires ahead of refusals that already exist and says less than they do. | It defers where `story.read_state()` or STORY-010 already answers. Caught by three existing tests failing, not by inspection. |
| This repository's ten stories are judged by a rule written after they were authored, two of them by hand before any validator existed. | Verified against the corpus before the contract was written, and held by the scenario *Every story in this repository passes the consistency rule*. |
| The branch resolves to STORY-010, whose readiness would permit this story's writes. | Named in `constraints.md` under Dependencies; the story has its own branch. |
