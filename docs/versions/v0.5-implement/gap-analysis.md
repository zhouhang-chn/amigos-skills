# v0.5 `/implement` — Gap Analysis

Story: **STORY-006**. Milestone exit criterion: *the project moves from a ready
contract to verified implementation without redefining the requirement.*

## Current state

| Piece | Exists | What it does |
|---|---|---|
| `amigos check` | v0.1 | Derives readiness from the contract files and writes `dor.json`, including a sha256 of each of the four input files under `contract_hash`. |
| `amigos gate` | v0.2 | Refuses a change to a governed path unless a resolvable story is ready. |
| `amigos hooks` | v0.2 | PreToolUse and pre-commit adapters for that refusal. |
| `/amigos` | v0.3, v0.4 | Produces a ready contract from a ticket using three independent role agents. |
| `amigos findings` | v0.4 | Counts what each role found that the others did not. |

Everything up to the contract exists. Nothing consumes one.

## Gaps

| # | Gap | Severity | Impact |
|---|---|---|---|
| 1 | No skill carries a contract into implementation. An agent reads it once, then implements from memory and chat. | High | Tests come to validate the implementation instead of the intent — the outcome README section 1 exists to prevent. |
| 2 | `contract_hash` is written by every evaluation and read by nothing. | High | "The requirement was not redefined" is a claim no command can check, so the milestone's exit criterion has no artifact. |
| 3 | README section 14 tells `/implement` to read `dor.json` for `"ready": true`; `docs/component-design/gate.md` states a committed verdict is a record and never an authority. | High | Building to the README would ship a readiness check weaker than the gate guarding the same writes, and would let an agent authorise itself by editing a file. |
| 4 | Responsibility 5, "run tests and evals", names an eval harness that does not exist. | Medium | Two of seven stated responsibilities cannot be performed as written; scope must narrow or the milestone stops being one change. |
| 5 | Responsibility 6, "check for scope expansion", names no basis of comparison. | Medium | Undefined, it is unimplementable; over-defined, it halts on false positives. |
| 6 | Nothing says what happens to a `Then` clause no test can observe. | Medium | This repository's own contracts contain such clauses, so the first target already carries the failure: skip the hard ones, report the contract as verified. |
| 7 | Nothing says where a run's report goes. | Medium | Coverage, changed files and unsatisfied scenarios are only reviewable if the run leaves a durable record. `/amigos` settled the equivalent with `.amigos/runs/`. |
| 8 | No lifecycle state means "implementation in progress", and declaring `contract_change` withholds readiness immediately. | Medium | On a contract conflict the gate then refuses to commit the partial work already in the tree. |
| 9 | No repository declares its test command in `.amigos/config.json`. | Low | "Run tests" resolves by convention here and to nothing downstream. |
| 10 | `tests/test_dogfooding.py` enumerates story ids as a literal tuple omitting STORY-006. | Low | Closing the milestone edits a governed test file as a side effect. |

## Non-goals

Carried from STORY-006's `## Out of Scope`, each with the reason it is deferred:

- **Mechanical prevention of contract edits.** v0.6 owns it; STORY-007 already
  excluded it from the gate. Here the rule is stated and its violation made
  visible, not made impossible.
- **Evals, golden tasks, graders.** Phase 7 / STORY-008.
- **A test-command key in `.amigos/config.json`.** A protocol schema change.
- **A lifecycle state meaning "implemented".** A change to the state schema and
  the validator.
- **`/implement` invoking `/amigos` on a conflict.** One session must not both
  discover a conflict and author the criterion replacing it.
- **Autonomous commits, branch creation, pull requests.**
- **Demonstrating the milestone on STORY-006.** The skill cannot build itself.

## Open questions

Non-blocking, carried from the contract:

- Can partial work survive a contract conflict, given that declaring
  `contract_change` withholds readiness and the gate then refuses the commit?
- Should the test command move into the protocol, or stay a repository
  convention?
- Should scope expansion eventually be judged semantically against `intent.md`
  rather than against the scenarios and Relevant Components?
- Writes made through `Bash` bypass the gate. `/implement` is the first skill
  that needs `Bash`, so that deferred hole now has its first consumer.

## The bootstrap problem

`/implement` cannot implement STORY-006: the skill would have to exist before it
could build itself, and STORY-001 through STORY-005 and STORY-007 are already
implemented. The decision on record is that **v0.6's first story is the
demonstration**, and v0.5 stays open until that run produces evidence. This
couples the two milestones' timelines deliberately, on the v0.4 precedent that a
milestone does not close on code that was never exercised.
