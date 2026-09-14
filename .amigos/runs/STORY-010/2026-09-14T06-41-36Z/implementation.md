# STORY-010 — implementation run

Run by `/implement` against the contract committed at `a39d448`. The contract was
not authored in this run; it came from the `/amigos` run recorded beside this
file at `2026-09-14T01-11-42Z`.

## Coverage

Ten scenarios, **10 of 10 decided by tests**. No scenario needed a judgement
method: every `Then` in this contract is observable through `gate.decide()` or
through the `amigos gate` command, which is the observable `intent.md` chose on
purpose so that the `PreToolUse` adapter inherits the rule rather than restating
it.

| Scenario | Decided by |
|---|---|
| An edit to a ready story's acceptance criteria is refused | `test_an_edit_to_a_ready_storys_acceptance_criteria_is_refused`, and its last `Then` by `test_the_refusal_does_not_tell_the_caller_to_make_the_story_ready` |
| Declaring a withholding state reopens the contract | `test_declaring_a_withholding_state_reopens_the_contract` |
| An edit that would leave the story unready is refused all the same | `test_an_edit_that_would_leave_the_story_unready_is_refused_all_the_same` |
| The commit that first records a ready contract is permitted | `test_the_commit_that_first_records_a_ready_contract_is_permitted` |
| A story that is not ready keeps an editable contract | `test_a_story_that_is_not_ready_keeps_an_editable_contract` |
| Only the contract inputs are frozen, not the records beside them | `test_only_the_contract_inputs_are_frozen_not_the_records_beside_them` |
| The refusal follows the story the path names, not the active one | `test_the_refusal_follows_the_story_the_path_names_not_the_active_one` |
| A story whose contract cannot be evaluated stays editable | `test_a_story_whose_contract_cannot_be_evaluated_stays_editable` |
| A staged deletion of a ready story's contract file is refused | `test_a_staged_deletion_of_a_ready_storys_contract_file_is_refused` |
| Scaffolding a new story is permitted while another story is ready | `test_scaffolding_a_new_story_is_permitted_while_another_story_is_ready` |

One scenario contributed a second test rather than a second assertion. The last
`Then` of scenario 1 — *the refusal does not tell the caller to make the story
ready* — is about what a human reads on stderr, so it is judged at the CLI.

## Red before green

`tests/test_gate_contract_freeze.py` was written in full and run against
unchanged source:

```text
8 failed, 3 passed in 2.08s
```

**The three that passed before any implementation are reported as passing, not
as red.** They are the over-refusal guards — a not-ready story keeps an editable
contract, an unevaluable story stays editable, scaffolding stays permitted — and
permitting is what the repository already did. Their value is that they must
*still* pass once the rule exists, which is the direction this story is most
likely to get wrong. Claiming them as red would have inflated the evidence.

Of the eight that failed, three failed with `TypeError` on the `staged=` argument
that did not exist yet, one failed because `staged_paths()` never reported the
deletion at all, and four failed on the refusal itself.

## Test results

```text
python -m pytest tests/test_gate_contract_freeze.py -q
11 passed in 2.96s

python -m pytest -q
343 passed in 19.99s
```

332 before this story, 343 after. No existing test changed.

Two existing tests were checked deliberately rather than by luck, because both
sit directly under the new rule:

- `test_a_change_touching_only_exempt_paths_needs_no_story` passes
  `.amigos/stories/X/intent.md` for a story that is not in the corpus. Under the
  new rule `X` cannot be evaluated, the rule fails open, and it stays permitted.
- `test_this_repository_exempts_the_work_that_makes_a_story_ready` asserts
  through `is_exempt()`, which is untouched. `.amigos/**` is still exempt; the
  refusal is a second question, not a change to the exempt set.

## Changed files

| File | Serves |
|---|---|
| `src/amigos/gate.py` | `contract_file()`, `frozen_contracts()`, `_ready_before_change()`, `_ready_at_head()` and the `staged` parameter — scenarios 1–8, 10, and the constraints on path origin, fail-open, and `classify()`'s semantics |
| `src/amigos/gate.py` (`staged_paths`) | scenario 9: `--diff-filter=ACMRT` gains `D`, so a staged deletion reaches a decision at all |
| `src/amigos/cli.py` (`_gate`) | scenario 1's last `Then`: a frozen-contract refusal names the reopening route instead of `Make the story ready` |
| `tests/test_gate_contract_freeze.py` | all ten scenarios |
| `docs/component-design/gate.md` | the `In Scope` bullet requiring the rule and its route to be recorded there |

### Scope expansion

One change serves no scenario and is reported rather than hidden:

- `skills/implement/SKILL.md:20` stated that the no-contract-edit rule *"has to
  hold without enforcement"*. That sentence became false the moment this story
  landed, and `constraints.md` lists the file under Relevant Components with
  exactly that note. Corrected to name the gate and the reopening route. It is a
  one-line factual correction to a shipped instruction, not new behaviour, but it
  was a judgement call and no scenario asked for it.

## Discrepancies

- **`working_tree_paths()` still omits deletions.** The contract names
  `gate.staged_paths()` and scenario 9 is a staged deletion, so only that
  collector was changed. `amigos gate` with no arguments therefore still misses a
  contract file deleted in the working tree. Recorded in `gate.md`'s known holes
  and left for a later story rather than widened silently.
- **`verify`'s git helpers were used more narrowly than `constraints.md`
  implies.** Dependencies names them for reading a contract at `HEAD`.
  `verify.work_tree_root()` is used, via a function-local import because
  `verify` imports `gate`; the blob read itself is a new `_git_bytes()` in
  `gate.py`, because `verify._git` raises `NoBaseline` and the gate needs its own
  `GateUnavailable` vocabulary to fail open rather than to exit 2.
- **README section 19 still describes this rule as text only.** Not in scope and
  not corrected; the README already carries outstanding corrections from v0.5.

## Verification

```text
amigos verify STORY-010     exit 0   baseline a39d44861080, four files MATCH
amigos status               exit 0   nine stories, all ready
amigos gate --staged        permitted
```

The rule was also exercised against this repository rather than only against
fixtures:

```text
amigos gate --changed-file .amigos/stories/STORY-007/acceptance.feature
  refused - story STORY-007 is ready and its contract may not be edited

amigos gate --changed-file .amigos/stories/STORY-010/intent.md
  refused - story STORY-010 is ready and its contract may not be edited

amigos gate --changed-file .amigos/stories/STORY-010/dor.json \
            --changed-file .amigos/stories/STORY-010/state.json
  permitted - no governed path was changed
```

The second of those is the story freezing its own contract. It is the intended
outcome and it held for the rest of this run: nothing in this slice edits a
contract input file.

## Unsatisfied scenarios

None. Every scenario has a passing test.

## Follow-ups

- `working_tree_paths()` and deletions, above.
- `.amigos/config.json` is exempt and carries `gate.exempt`, so a ready story
  still permits switching this rule off. Named in `open-questions.md` as a
  sibling of gap 5, and now in `gate.md`'s known holes.
- `tests/test_dogfooding.py` still enumerates story ids in a literal tuple and
  omits STORY-006, STORY-009 and STORY-010. Unchanged by this story and still the
  self-hosting invariant tested through an allowlist.
