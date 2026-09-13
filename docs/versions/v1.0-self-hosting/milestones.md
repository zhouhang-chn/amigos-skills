# v1.0 Self-Hosting — Milestones

| Version | Scope | Depends on | Exit criterion | Status |
|---|---|---|---|---|
| v0.1 | Contract format, deterministic validator, acceptance lint, scaffolding | — | Readiness can be rejected without asking a model. | Complete |
| v0.2 | Repository gate refusing source changes without a ready story | v0.1 | The project cannot casually bypass its own contract. | Complete |
| v0.3 | `/amigos` MVP, one orchestrator preserving the three logical phases | v0.2 | Amigos Skills can create usable contracts for its own development. | Complete |
| v0.4 | Product, Development and QA as independent subagents | v0.3 | A run records one findings record per role and a computed count of findings named by exactly one role, and that count is greater than zero. | Complete |
| v0.5 | `/implement` | v0.4 | The project moves from a ready contract to verified implementation without redefining the requirement. | Complete |
| v0.6 | Strong self-hosting enforcement, contract immutability | v0.5 | No privileged development path around the protocol. | In progress |
| v0.7 | Dogfooding failure corpus and evals | v0.6 | Every recurring failure class becomes a durable regression test. | Not started |

## Why v0.5 is now closed

v0.5's skill and its `amigos verify` command were built and tested in v0.5, but
the milestone's exit criterion could not be evaluated by the story that created
them: `/implement` would have to exist before it could implement itself.

**v0.6's first story was the demonstration**, on the v0.4 precedent that a
milestone does not close on code that was never exercised. STORY-009 was built by
running `/implement` against a contract it did not author, and the run record is
at `.amigos/runs/STORY-009/2026-09-13T23-05-08Z/implementation.md`: nine
scenarios, 9 of 9 decided by tests, red recorded before green, 332 tests passing,
`amigos verify STORY-009` exit 0 against the committed baseline.

The run also reported what it was supposed to report rather than what would have
looked better. It found that STORY-006's own contract was finalised in the same
commit that implemented it, so that story no longer verifies under the baseline
v0.6 introduced. Recorded, not repaired.

## Notes on ordering

v0.2 precedes v0.3 deliberately. README section 32 places the repository gate
before agent orchestration: an unenforced rule is a suggestion, and automating
reasoning on top of a suggestion produces confident output nobody has to honour.

v0.4 carries a genuine kill criterion. If independent subagents only produce
duplicated prose, the multi-agent design does not survive the milestone.

Its exit criterion was reworded during v0.3. The original — "the three agents
discover different classes of ambiguity, scope risk and failure mode" — never
defined *different*, so nothing could judge it. The `/amigos` run that drafted
STORY-005 found that in its challenge pass and escalated it to the interview,
which is the intended path working. A kill criterion nobody can evaluate is how
a design survives without earning it.
