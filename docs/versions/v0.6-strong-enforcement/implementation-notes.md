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
