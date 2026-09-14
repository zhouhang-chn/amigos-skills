# v0.6 Strong Self-Hosting Enforcement — Implementation Notes

## STORY-009 — contract immutability

Built by running `/implement` against the contract, in the session that drafted
it but not the one that wrote the skill. The run record, with full coverage and
scope reporting, is at
`.amigos/runs/STORY-009/2026-09-13T23-05-08Z/implementation.md`.

### What was built

| Piece | What it is |
|---|---|
| `verify.baseline_revision()` | Oldest commit touching the contract, then the oldest governed commit after it, then that commit's parent |
| `verify.evaluate()` | Compares the working tree to that revision through `git diff`, not by hashing bytes against a blob |
| `verify.work_tree_root()` | The git root, which is not necessarily `Config.root` |
| `verify.recorded_hashes()` | `dor.json.contract_hash`, demoted from authority to record |
| `tests/test_verify_baseline.py` | 12 cases, one per scenario plus the no-git case `constraints.md` names |
| `tests/conftest.py::committed_repo` | The fixture the story needed and the repository did not have |

### Decisions taken during implementation

**The baseline is derived, never recorded.** Writing the baseline revision into
`dor.json` would have been simpler and would have recreated the exact problem the
story exists to solve: a file that says where the contract started, writable by
the agent being judged.

**`git diff` rather than a hash comparison.** QA found this and Development
turned it into a constraint. Hashing working-tree bytes against a blob is not
equality-safe under `core.autocrlf`, `text=auto` or any clean filter, and this
checkout has no `.gitattributes`, so the defect would have shipped invisibly and
surfaced in somebody else's repository.

**Governed is `gate.classify()`.** Not a second definition of the same idea.
Two implementations of one rule drift, and the drift is invisible until the rule
is wrong.

**`git rev-list`, not `git log --follow`.** An early reading of history used
`--follow` and reported STORY-006's contract as reaching back to `564a68f`, a
commit that does not touch the story directory at all. `--follow` was tracing a
rename through content similarity. The wrong query would have produced a
plausible, wrong baseline.

### The fixture migration was the larger half

Every `verify` test in the repository ran on `scratch_repo`, which is not a git
repository, and nothing in `test_verify.py` used the `git_repo` fixture that
already existed. Moving the baseline into git therefore broke twelve passing
tests by construction.

They were migrated rather than deleted, because what they assert — readiness is
re-derived, a moved contract is named, `verify` writes nothing — is true
independently of where the baseline is kept. Two were genuinely superseded and
were re-pointed rather than dropped:

- `test_no_baseline_is_a_structural_error` — "no baseline" now means no committed
  contract rather than an absent `dor.json`. Same refusal, new cause.
- `test_a_baseline_without_hashes_is_a_structural_error` became
  `test_a_recorded_hash_is_no_longer_required_to_verify`, which asserts the
  demotion directly.

### What the mechanism found on its first use

`amigos verify STORY-006` now exits 1. STORY-006's contract was finalised in
`2e8d1d8`, the same commit that implemented it, so the baseline falls on the
commit before, where the contract was still a scaffold.

This is a true finding about the repository's history, not a defect. README
section 30 asks that history show contract change and implementation change as
separate concepts; v0.5's slice did not, and the first thing v0.6 built noticed.
It is recorded rather than repaired — rewriting history to make a check pass is
the failure this milestone exists to prevent, performed at a larger scale.

### Reported rather than done

`tests/test_dogfooding.py` still enumerates story ids in a literal tuple omitting
STORY-006 and STORY-009. No scenario in this contract asks for it. It is gap 9
and belongs to whichever story next touches the dogfooding corpus.

### Verification results

```text
python -m pytest -q          332 passed
amigos verify STORY-009      exit 0, baseline c9966ac454c1, four files MATCH
amigos status                exit 0, all eight stories ready
amigos gate --staged         permitted, STORY-009 (branch name)
```

## STORY-010 — the gate refuses a contract edit while a story is ready

Built by running `/implement` against a contract this session drafted through
`/amigos` but did not author by hand. The run record is at
`.amigos/runs/STORY-010/2026-09-14T06-41-36Z/implementation.md`.

### What was built

| Piece | What it is |
|---|---|
| `gate.contract_file()` | A changed path mapped to `(story_id, file)` through `config.stories_dir`, never through the literal prefix `.amigos/stories/` |
| `gate._ready_before_change()` | The working tree at edit time, `HEAD` at commit time, failing open on anything unevaluable |
| `gate._ready_at_head()` | The four contract inputs read from `HEAD`, the live `state.json` beside them, evaluated through an overridden `stories_dir` |
| `gate.frozen_contracts()` | One verdict per story however many of its files were touched |
| `Decision.frozen` | Additive in `--json`; `story_id` keeps meaning the resolved active story |
| `cli._gate()` | A frozen-contract refusal names the reopening route, not `Make the story ready` |
| `tests/test_gate_contract_freeze.py` | 11 cases: one per scenario, plus the CLI surface for scenario 1's last `Then` |

### Decisions taken during implementation

**A second question, not a wider exempt set.** `classify()` keeps its path-only,
time-independent meaning because `verify._governed_in()` runs it over historical
commits. Expressing the freeze as "a ready story's contract is governed" would
have judged past commits by present-day readiness and moved the baseline
STORY-009 was built to fix. The rule is asked alongside classification instead.

**The fail-open direction is inverted from the gate's default, so it is stated.**
Only a story that demonstrably evaluates ready freezes its contract. That is not
a weakening chosen for convenience: a contract with unparseable Gherkin must stay
editable or it can never be repaired.

**`_git_bytes()` in `gate.py` rather than reusing `verify._git`.** The contract's
Dependencies names `verify`'s helpers, and `verify.work_tree_root()` is used
through a function-local import — `verify` imports `gate`, so the module-level
direction is fixed. The blob read is separate because `verify._git` raises
`NoBaseline`, which exits 2, and the gate needs to fail *open* here rather than
report that it could not tell.

### The three tests that passed before the implementation

`tests/test_gate_contract_freeze.py` was run red first and reported
`8 failed, 3 passed`. The three passing ones are the over-refusal guards — a
not-ready story keeps an editable contract, an unevaluable story stays editable,
scaffolding stays permitted.

They are recorded as passing rather than as red. Permitting is what the
repository already did, so they proved nothing before the change; their value is
that they must still pass afterwards, which is the direction this story was most
likely to break. Counting them as red would have inflated the red-before-green
evidence, which is the one claim the phase exists to make honestly.

### The rule was exercised against this repository, not only fixtures

```text
amigos gate --changed-file .amigos/stories/STORY-007/acceptance.feature
  refused - story STORY-007 is ready and its contract may not be edited
amigos gate --changed-file .amigos/stories/STORY-010/intent.md
  refused - story STORY-010 is ready and its contract may not be edited
```

The second is the story freezing its own contract, which is the intended outcome
and held for the rest of the run.

### Reported rather than done

- `working_tree_paths()` still omits deletions. The contract names
  `staged_paths()` and scenario 9 is a staged deletion, so only that collector
  changed. Recorded in `gate.md`'s known holes.
- `.amigos/config.json` carries `gate.exempt`, is itself exempt, and a ready
  story still permits editing it — an unguarded off switch for this very rule.
  Named in `open-questions.md` and in `gate.md`.
- `tests/test_dogfooding.py` still omits STORY-006, STORY-009 and STORY-010.

### Scope expansion

`skills/implement/SKILL.md:20` claimed the no-contract-edit rule *"has to hold
without enforcement"*. That became false when this story landed, and
`constraints.md` lists the file under Relevant Components with that exact note.
Corrected to name the gate and the reopening route. No scenario asked for it.

### Verification results

```text
python -m pytest -q          343 passed (332 before)
amigos verify STORY-010      exit 0, baseline a39d44861080, four files MATCH
amigos status                exit 0, all nine stories ready
amigos gate --staged         permitted, STORY-010 (branch name)
```

## STORY-011 — contract state evidence and blocked stories

Built by running `/implement` against the contract committed at `c35704b`.
Run record: `.amigos/runs/STORY-011/2026-09-14T10-05-00Z/implementation.md`.

Taken ahead of milestone tasks 3 and 4 because STORY-010 made it load-bearing:
the freeze that shipped two commits earlier reads its unlock from `state.json`,
and nothing verified that file.

### What was built

`gate.py` gained a third question, asked before the contract freeze. A story's
lifecycle record must hold together — `declared_state` and `updated_at` are the
ones its last history entry records, and the committed history is still a prefix
of the current one — or every governed write for that story is refused.

`amigos state <ID>` with no `--set` became the report: 0 consistent, 1
inconsistent, 2 could not read. `--set` is now optional rather than required, so
the surface is additive and no exit vocabulary was extended.

A blocked story's refusal now names its derived state, a failed check, and
re-contracting through the amigos skill. It previously ended `Make the story
ready, then retry: amigos check <id>`, naming a command that returns the same
verdict on a story that fails a check.

### The finding that changed the story

The ticket asked for detection of a hand-edited `state.json`. Development and QA
found independently that this is unbuildable: with no key, no signature and no
writer identity, a well-formed hand edit is byte-identical to what `set_state()`
writes. The contract narrowed to detecting an *unrecorded* change — gap 8's own
wording — and recorded the narrowing under `## Out of Scope`.

This is worth keeping visible. A run that had quietly shipped "detects a
hand-edited state.json" would have left the milestone claiming a protection
nothing implements.

### Decisions

- **The refusal is a gate decision, never a readiness verdict.** Routing it
  through readiness would have inverted it: `frozen_contracts()` freezes only a
  story that demonstrably evaluates ready, so a tampered story reported as not
  ready would have had its contract *released*. Detection would have widened the
  hole it closes.
- **Asked before the freeze**, because the freeze reads `state.json` live.
- **A write to a story's own `state.json` stays permitted**, since `set_state()`
  parses before writing and a corrupt record could otherwise never be repaired.
  Erasing committed history is the exception; that is never repair.
- **Strict over loose consistency.** The loose reading — "some entry records this
  state" — passes `draft` declared over `[draft, amigos_running]`, which is a
  mid-run rollback. The strict reading is what `set_state()` already guarantees.
- **Defer where a louder rule already speaks.** An undeclarable `declared_state`
  is refused by `story.read_state()`; a story directory that does not exist was
  settled by STORY-010. Both defer rather than being restated.

### Red before green, and the part that was not red

`tests/test_gate_lifecycle.py` ran against unchanged source first:
**11 failed, 2 passed.**

The two that passed are reported as passing rather than counted as red:

- *Declaring contract_change still reopens a frozen contract* — STORY-010's
  shipped rule, held here as a regression guard.
- *No declarable state makes a blocked story permit a governed change* — already
  true, because a blocked story is refused whatever it declares.

Both are guards against over-refusal, and permitting is what the repository
already did. Claiming them as red would have inflated the evidence.

### Three shipped tests failed, and the rule changed rather than the tests

The first full-suite run after the new tests went green was **3 failed, 353
passed**. All three were existing tests, and all three were right:

- `test_a_story_whose_contract_cannot_be_evaluated_stays_editable` (STORY-010)
  and `test_a_change_touching_only_exempt_paths_needs_no_story` — a path naming a
  story directory that does not exist was being refused as an unreadable record.
- `test_a_story_that_cannot_be_evaluated_refuses_rather_than_raising` — the new
  question fired ahead of `story.read_state()`'s "not declarable" refusal and
  replaced a more precise message with a vaguer one.

The fix was in `lifecycle_report()`, not in the tests: it now returns *unanswered*
for a story directory that does not exist, and defers to `read_state()` when
`declared_state` is not declarable at all. A story directory that exists but has
lost its `state.json` is still refused, so deleting the record is not cheaper
than corrupting it.

No existing test was modified.

### Exercised against this repository

Not only against fixtures:

- hand-writing `contract_change` into `.amigos/stories/STORY-007/state.json` and
  then editing its `acceptance.feature` is refused, where before this story the
  edit was permitted;
- deleting a committed history entry from that record is refused;
- deleting the record entirely is refused;
- `amigos state STORY-010` reports the record consistent, exit 0.

### Verification

```text
python -m pytest -q        356 passed  (343 before, 13 new)
amigos check STORY-011     exit 0, ready
amigos verify STORY-011    exit 0, verified: true, baseline c35704b92426
amigos status              exit 0, ten stories ready
amigos gate                permitted - story STORY-011 (branch name) is ready
```

### Discrepancies

- `constraints.md` lists `tests/fixtures/stories/RUNNING-001/state.json` as a
  record the rule rejects and says making it coherent should be planned rather
  than discovered. It was left as it is: the rule lives in the gate, no test
  reaching that fixture runs the gate, and editing it would have changed a
  fixture no scenario covers. It stays a non-blocking question.
- `constraints.md` names `gate._git_bytes()` and `verify.work_tree_root()` as the
  dependencies for reading the committed copy. Both were used, but through a new
  `_work_tree_relative()` helper the contract did not anticipate.
- The contract's In Scope names only `docs/component-design/gate.md` for the
  record. The version docs under `docs/versions/v0.6-strong-enforcement/` were
  also updated, as the repository's standing documentation workflow requires.

## Follow-ups

- README section 14 still tells `/implement` to read `dor.json` for readiness.
  Outstanding since v0.5.
- README section 0's status table still lists `/implement` as "Not built".
- `docs/component-design/execution.md` closes with "an open question for v0.6"
  about partial work surviving a contract conflict. Still open.
- Decide whether v0.5's implementation notes should record that STORY-006 no
  longer verifies under the v0.6 baseline.
- `working_tree_paths()` does not collect deletions, so `amigos gate` with no
  arguments misses a contract file deleted in the working tree.
- `.amigos/config.json` is an unguarded off switch for the contract freeze. It is
  the sibling of gap 5 and is owned by neither gap 5 nor STORY-010.
- README section 19 still describes the no-contract-edit rule as text only.
- `schemas/state.schema.json` is enforced only by `tests/test_dogfooding.py`,
  over an allowlist of story ids, so this repository holds itself to a check it
  does not ship to adopters.
- `amigos state --set` accepts a transition with no `--note`, so a sanctioned
  reopening can carry no reason at all.
- `tests/fixtures/stories/RUNNING-001/state.json` declares `amigos_running` while
  its only history entry is `draft`, which the shipped rule rejects. Harmless
  today; a trap for the next gate test written over that fixture.
- A history rewrite committed with `--no-verify` is invisible afterwards, because
  the append-only comparison is against HEAD. The commit is refused at the
  pre-commit adapter, so it takes a second deliberate bypass. Gap 4.
- The `amigos` console script is not installed in the development environment;
  the git hooks work regardless because they insert `src/` on `sys.path`.
