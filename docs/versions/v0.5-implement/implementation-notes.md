# v0.5 `/implement` — Implementation Notes

Story: **STORY-006**. Branch: `story/STORY-006-implement-skill`.

## Status: built, demonstration deferred by design

The skill and its verification command are built, tested and pass every closeout
check. The milestone's exit criterion — *the project moves from a ready contract
to verified implementation without redefining the requirement* — **has not been
evaluated**, because `/implement` cannot implement the story that creates it.

That is not a shortfall discovered late; it was decided at contract time and is
recorded in STORY-006's `## Out of Scope`. **v0.6's first story is the
demonstration**, and `milestones.md` keeps v0.5 open until that run produces
evidence. The v0.4 precedent applies directly: a milestone does not close on code
that was never exercised.

## What was built

| Piece | What it is |
|---|---|
| `src/amigos/verify.py` | Re-derives readiness, diffs the four contract files against `dor.json.contract_hash`, computes `verified = ready and not changed` |
| `amigos verify <STORY-ID>` | Exit 0 verified, 1 not verified, 2 structurally unanswerable; `--json` for a caller |
| `skills/implement/SKILL.md` | Six phases, six prohibitions, the conflict path that stops rather than re-contracts |
| `.claude/skills/implement` | Symlink, so the checkout runs the file the plugin ships |
| `tests/test_verify.py` | 11 cases, including the stale-verdict case the command exists for |
| `tests/test_skill_implement.py` | 23 cases holding the prompt to the code |
| `tests/test_cli.py` | 5 added cases for registration and exit codes |

## Decisions taken during implementation

### `contract_hash` was already there; nothing had ever read it

`dor.json` has carried a sha256 of each contract input file since v0.1. The
milestone's exit criterion is exactly the question that field answers, so
`verify` is a comparison that was 90% built and never wired up. No new persisted
artifact was added.

### Readiness is recomputed, and the README is the text that is wrong

All three drafting roles found the contradiction: README section 14 tells
`/implement` to read `dor.json` for `"ready": true`; `docs/component-design/gate.md`
states a committed verdict is a record and never an authority. It was resolved
toward the code. `verify` calls `dor.evaluate()` and reads `dor.json` for one
thing only — the recorded hash baseline.

`test_a_stale_ready_verdict_never_produces_a_pass` is that decision as a test: it
breaks a contract, hand-edits `dor.json` back to `ready: true`, and asserts the
command still refuses. Built to the README, that test would fail.

**Follow-up: README section 14 needs correcting.** It is documentation, so it did
not block this slice.

### What `verify` deliberately does not catch

An agent that edits `acceptance.feature` **and then re-runs `amigos check`**
rewrites the baseline, and `verify` passes.

The hole is real and left open on purpose. Closing it means comparing against git
history rather than the working tree, which is contract immutability, which
STORY-006 put out of scope and v0.6 owns. Implementing it here would have been a
milestone doing the next milestone's job. What `verify` catches is the case that
actually occurs: a contract edited during implementation and left behind.

### The skill declares `contract_change` last

Development alone found this during drafting: declaring `contract_change`
withholds readiness immediately, after which the gate refuses every governed
write, including committing the partial implementation already in the tree. So
the skill's conflict path reports first and declares last.
`test_the_skill_declares_contract_change_last` asserts that ordering in the text.

### The skill never invokes `/amigos`

A session that both discovers a conflict and authors the criterion replacing it
has no independent perspective between the two. This was put to the user at
contract time and settled as: report, declare, stop, hand to a human.

### Tests were made whitespace-insensitive, not the prose reflowed

Two assertions initially failed because the phrases they matched span a line
break in the skill file. The fix was a `flowed` fixture that collapses
whitespace. Reflowing the document to satisfy a substring match would be the test
dictating the prose's shape, and the assertion's meaning is that the skill *says*
a thing, not that it says it on one line.

## Scope expansion, reported rather than done

The contract's own rule is to report a change no scenario requires rather than
keep it quietly. Two candidates came up and **neither was made**:

- **`tests/test_dogfooding.py` still omits STORY-006** from its literal
  `STORY_IDS` tuple. Adding it is a governed edit no scenario in this contract
  asks for. It belongs to whichever story next touches the dogfooding corpus.
- **A `--since-head` baseline for `verify`.** Strictly better detection, and
  squarely v0.6's contract immutability.

## Two scenarios are not decided by tests

Per the contract's own rule about `Then` clauses no test can observe, these are
named with the judgement method used instead, and excluded from the test-decided
count:

| Scenario | Judged by |
|---|---|
| *A test for absent behaviour fails before the source changes* | The instruction's presence in `skills/implement/SKILL.md`, asserted by `test_the_skill_requires_red_before_green`. Whether an agent obeys it cannot be observed from here. |
| *The run takes no privileged path around the gate* | The prohibition's presence in the skill, asserted by `test_the_skill_forbids_a_privileged_path_around_the_gate`. |

The other eight scenarios are decided by tests. **8 of 10 test-decided** is the
honest coverage number, and it is stated here rather than rounded up — the same
limit `tests/test_skill.py` already documents for `/amigos`.

This slice did follow the red-before-green rule itself: `tests/test_verify.py`
was written first and run against an absent module, failing with
`ImportError: cannot import name 'verify'`, before `src/amigos/verify.py` existed.

## Verification results

```text
python -m pytest -q                     320 passed
amigos check STORY-006                  exit 0, ready
amigos verify STORY-006                 exit 0, verified: true, four files MATCH
amigos status                           exit 0, all seven stories ready
amigos gate --staged                    permitted, STORY-006 (branch name)
```

No `.amigos/runs/STORY-006/*/implementation.md` exists, and none was written.
The skill was hand-built, not run; writing an implementation run record would
claim evidence this milestone does not have.

## Follow-ups

- **v0.6's first story is run through `/implement`.** That produces v0.5's exit
  evidence and is the first genuine test of the skill. It must be a fresh
  session: skills are snapshotted at registration, so the session that writes a
  skill serves its pre-edit text.
- **Correct README section 14** to recompute readiness rather than read
  `dor.json`, matching `gate.py` and `verify.py`.
- **README section 0's status table** lists `/implement` as "Not built" and needs
  updating when the demonstration lands.
- `tests/test_dogfooding.py` should cover STORY-006, under a story that asks for
  it.
