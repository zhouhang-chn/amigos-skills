# STORY-009 — implementation run

Skill: `/implement`. Branch: `story/STORY-009-contract-immutability`.
Contract baseline: `c9966ac` ("Contract: STORY-009, contract immutability").

This is the first run of `/implement` against a contract it did not create, and
it is the evidence v0.5's exit criterion has been held open for.

## Coverage

Nine scenarios, **9 of 9 decided by tests**. No scenario in this contract asserts
agent behaviour or prompt text, so none needed a judgement method instead of a
test — unlike STORY-006, which reported 8 of 10.

| Scenario | Decided by |
|---|---|
| An unchanged contract verifies against its committed baseline | `test_an_unchanged_contract_verifies_against_its_committed_baseline`, `test_the_baseline_names_the_revision_in_its_serialised_form`, `test_verify_writes_no_file_inside_the_story_directory` |
| The baseline is the parent of the first governed change | `test_the_baseline_is_the_parent_of_the_first_governed_change` |
| Re-running the readiness check does not launder a contract edit | `test_re_running_the_readiness_check_does_not_launder_a_contract_edit` |
| A contract edit committed during implementation does not become the baseline | `test_a_committed_contract_edit_does_not_become_the_baseline` |
| A contract that was never committed is unanswerable | `test_a_contract_that_was_never_committed_is_unanswerable` |
| A readiness verdict written by hand produces no pass | `test_a_readiness_verdict_written_by_hand_produces_no_pass` |
| A change outside the story directory is not a contract change | `test_a_change_outside_the_story_directory_is_not_a_contract_change` |
| A contract rewritten through contract_change stays verifiable | `test_a_contract_rewritten_through_contract_change_stays_verifiable` |
| A configured content filter does not produce a difference | `test_a_configured_content_filter_does_not_produce_a_difference` |

## Red before green

`tests/test_verify_baseline.py` was written first and run against the unchanged
source:

```text
11 failed in 2.07s
E  AttributeError: module 'amigos.verify' has no attribute 'baseline_revision'
E  amigos.verify.NoBaseline: .../READY-001/dor.json: no recorded contract hash
```

One of those eleven failed for the wrong reason after the implementation landed:
`test_a_contract_that_was_never_committed_is_unanswerable` had been written
against a directory with no git at all, while the scenario says *"a story whose
four contract files appear in no commit"* — a git repository with an uncommitted
contract. The test was corrected to match the scenario, and a separate test was
added for the no-git case, which `constraints.md` covers rather than
`acceptance.feature`.

## Test results

```text
python -m pytest -q                     332 passed in 14.78s
amigos verify STORY-009                 exit 0, baseline c9966ac454c1, four files MATCH
amigos status                           exit 0, all eight stories ready
amigos gate --staged                    permitted, STORY-009 (branch name)
```

## Changed files

| File | Serves |
|---|---|
| `src/amigos/verify.py` | all nine scenarios; the baseline derivation and the git comparison |
| `src/amigos/cli.py` | *An unchanged contract verifies…* — "the output names the git revision" |
| `tests/test_verify_baseline.py` | the nine scenarios |
| `tests/conftest.py` | `constraints.md` Dependencies: the only git-backed fixture was `git_repo`, and none of the `verify` tests used it |
| `tests/test_verify.py` | same; the v0.5 tests ran on a non-git fixture and could not survive a git baseline |
| `tests/test_cli.py` | same |

No scope expansion. Every changed file traces to a scenario or to a stated
constraint.

**Not done, and reported instead:** `tests/test_dogfooding.py` still enumerates
story ids in a literal tuple that omits both STORY-006 and STORY-009. Adding them
is a governed edit no scenario in this contract asks for. It is gap 9 of the v0.6
gap analysis and belongs to whichever story next touches the dogfooding corpus.

## Unsatisfied scenarios

None.

## Discrepancies

### The mechanism failed the repository on its first use, correctly

`amigos verify STORY-006` now exits 1, reporting all four contract files as
differing from the baseline `5ed6fea`.

This is not a false positive. STORY-006's contract first appears in history at
`5ed6fea` as a scaffold, and was finalised in `2e8d1d8` — **the same commit that
implemented it**. The first governed change for that story is therefore the
commit that also moved its contract, so the baseline is the commit before, where
the contract was still a scaffold.

README section 30 asks that history show contract change and implementation
change as separate concepts. v0.5's slice did not, and the mechanism built here
detected it the first time it was pointed at the repository. The finding is left
standing rather than papered over; rewriting that history would be a worse act
than recording the violation.

This does not affect readiness, `amigos status`, or `tests/test_dogfooding.py`,
all of which pass. It does mean v0.5's implementation notes record
`amigos verify STORY-006 → exit 0`, which was true under the mechanism in force
at the time and is not true under this one.

### `verify` was wrong about `--follow`

An early reading of history used `git log --follow`, which reported STORY-006's
contract as reaching back to `564a68f`. `--follow` was tracing a rename: that
commit does not touch the story directory at all. `rev-list` without it is the
correct query and is what the implementation uses.

### STORY-006's contract describes a superseded mechanism

Three of its scenarios name "the hash recorded in dor.json" as what verification
compares against. That is no longer the authority. STORY-006 is closed and its
contract is not editable from here; recorded as a follow-up.

## Follow-ups

- Correct README section 14, still outstanding from v0.5.
- README section 0's status table still lists `/implement` as "Not built".
- `tests/test_dogfooding.py` should cover STORY-006 and STORY-009.
- Decide whether v0.5's implementation notes should record that STORY-006 no
  longer verifies under the v0.6 baseline.
