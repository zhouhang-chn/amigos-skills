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

## Follow-ups

- README section 14 still tells `/implement` to read `dor.json` for readiness.
  Outstanding since v0.5.
- README section 0's status table still lists `/implement` as "Not built".
- `docs/component-design/execution.md` closes with "an open question for v0.6"
  about partial work surviving a contract conflict. Still open.
- Decide whether v0.5's implementation notes should record that STORY-006 no
  longer verifies under the v0.6 baseline.
