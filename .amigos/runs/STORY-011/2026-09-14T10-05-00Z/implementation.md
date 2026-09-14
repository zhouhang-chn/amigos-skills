# STORY-011 — implementation run

Contract: `.amigos/stories/STORY-011/`, committed at `c35704b`.
Branch: `story/STORY-011-contract-state-evidence`.
Test command: `python -m pytest -q`.

## Coverage

Twelve scenarios. **12 of 12 decided by tests.** No scenario needed a judgement
method; every `Then` in this contract is observable through `gate.decide()` or
through the CLI.

| Scenario | Decided by |
|---|---|
| A declared state the history does not record is refused | `test_a_declared_state_the_history_does_not_record_is_refused`, and `test_that_refusal_does_not_tell_the_caller_to_make_the_story_ready` for the last `Then` at the CLI |
| A history entry removed after it was committed is refused | `test_a_history_entry_removed_after_it_was_committed_is_refused` |
| A governed change under a blocked story is refused with the route out | `test_a_governed_change_under_a_blocked_story_is_refused_with_the_route_out` |
| A reopening recorded through the state command is permitted | `test_a_reopening_recorded_through_the_state_command_is_permitted` |
| Declaring contract_change still reopens a frozen contract | `test_declaring_contract_change_still_reopens_a_frozen_contract` |
| The commit that would launder a rewritten history is refused | `test_the_commit_that_would_launder_a_rewritten_history_is_refused` |
| A write to the story's own state.json is permitted while the record is inconsistent | `test_a_write_to_the_storys_own_state_json_is_permitted_while_inconsistent` |
| A state.json that cannot be parsed is refused rather than permitted | `test_a_state_json_that_cannot_be_parsed_is_refused_rather_than_permitted` |
| A state.json that was never committed is not reported as inconsistent | `test_a_state_json_that_was_never_committed_is_not_reported_as_inconsistent` |
| No declarable state makes a blocked story permit a governed change | `test_no_declarable_state_makes_a_blocked_story_permit_a_governed_change` |
| Every story in this repository passes the consistency rule | `test_every_story_in_this_repository_passes_the_consistency_rule` |
| The report writes nothing | `test_the_report_writes_nothing` |

Two scenarios needed their `Given` read carefully rather than loosely. *A write
to the story's own state.json is permitted while the record is inconsistent* and
*The commit that would launder a rewritten history is refused* look contradictory
— one permits a `state.json` write, the other refuses it. They are not: the first
describes a `declared_state` that disagrees with its last history entry, which is
what repair looks like; the second describes history entries removed, which is
never repair. The first draft of both tests used a helper that replaced the
history wholesale, which made the first scenario's fixture an instance of the
second. The tests were corrected to match their `Given` clauses.

## Red before green

`tests/test_gate_lifecycle.py` was written first and run against unchanged
source:

```text
11 failed, 2 passed
```

The two that passed are **reported as passing, not counted as red**:

- *Declaring contract_change still reopens a frozen contract* — STORY-010's
  shipped rule, carried here as a regression guard.
- *No declarable state makes a blocked story permit a governed change* — already
  true, because a blocked story is refused whatever it declares.

Both are over-refusal guards, and permitting is what the repository already did.
Their value is that they must still pass afterwards, which is the direction this
change was most likely to break. Claiming them as red would have inflated the
evidence the phase exists to produce honestly.

## Test results

```text
python -m pytest tests/test_gate_lifecycle.py -q     13 passed
python -m pytest -q                                  356 passed
```

343 before this story, 13 added. **No existing test was modified.**

An intermediate full-suite run reported `3 failed, 353 passed`. All three
failures were existing tests and all three were right; the rule was changed, not
the tests. See Discrepancies.

## Changed files

| File | Serves |
|---|---|
| `src/amigos/gate.py` | The whole contract: `story_file()`, `lifecycle_file()`, `LifecycleReport`, `lifecycle_report()`, `lifecycle_refusals()`, and the question asked in `decide()` before the freeze |
| `src/amigos/cli.py` | Scenarios *A governed change under a blocked story...*, *A reopening recorded through the state command...*, *A state.json that was never committed...*, *The report writes nothing*: `--set` made optional, `_state_report()`, and the two refusal surfaces |
| `tests/test_gate_lifecycle.py` | One test per scenario |
| `docs/component-design/gate.md` | `intent.md` In Scope: "The rule and its limits recorded in `docs/component-design/gate.md`" |
| `docs/versions/v0.6-strong-enforcement/{design,action-plan,implementation-notes}.md` | The repository's standing documentation workflow, not a scenario |

### Scope expansion

None. `contract_file()` was refactored onto a new `story_file()` rather than
duplicated, which is the same rule serving one more caller, and `--set` became
optional rather than changing meaning — an additive surface, as
`constraints.md` requires.

## Unsatisfied scenarios

None.

## Discrepancies

**Three shipped tests failed, and the rule was wrong rather than the tests.**

- `test_a_story_whose_contract_cannot_be_evaluated_stays_editable` (STORY-010's
  own scenario) and `test_a_change_touching_only_exempt_paths_needs_no_story`:
  a path naming a story directory that does not exist was refused as an
  unreadable record. `constraints.md` names STORY-010's fail-open rule as a
  shipped contract that this story may not change as a side effect, so
  `lifecycle_report()` now returns *unanswered* for a story directory that does
  not exist.
- `test_a_story_that_cannot_be_evaluated_refuses_rather_than_raising`: the new
  question fired ahead of `story.read_state()`'s "not declarable" refusal and
  replaced a precise message with a vaguer one. `lifecycle_report()` now defers
  when `declared_state` is not declarable at all — declaring a state you do not
  own is a louder failure than declaring one your history does not record, and it
  already has an implementation.

A story directory that exists but has lost its `state.json` is still refused, so
deleting the record is not cheaper than corrupting it. That case is covered by no
scenario in either story and is recorded in `gate.md`.

**`constraints.md` assumptions that did not hold as written.**

- It lists `tests/fixtures/stories/RUNNING-001/state.json` as a record the rule
  rejects and says making it coherent should be planned rather than discovered.
  It was left unchanged: the rule lives in the gate, no test reaching that
  fixture runs the gate, and editing a fixture no scenario covers would have been
  scope expansion. It stays a non-blocking question.
- It names `gate._git_bytes()` and `verify.work_tree_root()` as the dependencies
  for reading the committed copy. Both were used, but through a new
  `_work_tree_relative()` helper the contract did not anticipate.

**A non-blocking open question the work did not force.** None of the six was
decided silently.

**Environment.** The `amigos` console script is not installed in this
development environment (`command not found`). The git hooks are unaffected —
both insert `src/` on `sys.path` — and the commands in this record were run
through an equivalent shim.

## Exercised against this repository

Not only against fixtures:

```text
hand-write contract_change into STORY-007/state.json, then edit its contract
  refused - story STORY-007's lifecycle record does not hold together
delete a committed history entry from STORY-007/state.json
  refused - state.json no longer records the 'draft' entry committed at ...
delete STORY-007/state.json entirely
  refused - state.json cannot be read: ...: missing
amigos state STORY-010
  draft, 3 entries in history, lifecycle record: consistent, exit 0
```

Before this story, the first of those edits was permitted.

## Verification

```text
python -m pytest -q        356 passed
amigos check STORY-011     exit 0, ready
amigos verify STORY-011    exit 0, verified: true, baseline c35704b92426
amigos status              exit 0, ten stories ready
amigos gate                permitted - story STORY-011 (branch name) is ready
```

## Follow-ups raised

- `schemas/state.schema.json` is enforced only by `tests/test_dogfooding.py`,
  over an allowlist of story ids.
- `amigos state --set` accepts a transition with no `--note`.
- `tests/fixtures/stories/RUNNING-001/state.json` violates the shipped rule.
- A history rewrite committed with `--no-verify` is invisible afterwards (gap 4).
