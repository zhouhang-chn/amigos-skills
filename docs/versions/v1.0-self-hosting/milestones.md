# v1.0 Self-Hosting — Milestones

| Version | Scope | Depends on | Exit criterion | Status |
|---|---|---|---|---|
| v0.1 | Contract format, deterministic validator, acceptance lint, scaffolding | — | Readiness can be rejected without asking a model. | Complete |
| v0.2 | Repository gate refusing source changes without a ready story | v0.1 | The project cannot casually bypass its own contract. | Complete |
| v0.3 | `/amigos` MVP, one orchestrator preserving the three logical phases | v0.2 | Amigos Skills can create usable contracts for its own development. | Complete |
| v0.4 | Product, Development and QA as independent subagents | v0.3 | A run records one findings record per role and a computed count of findings named by exactly one role, and that count is greater than zero. | Complete |
| v0.5 | `/implement` | v0.4 | The project moves from a ready contract to verified implementation without redefining the requirement. | In progress |
| v0.6 | Strong self-hosting enforcement, contract immutability | v0.5 | No privileged development path around the protocol. | Not started |
| v0.7 | Dogfooding failure corpus and evals | v0.6 | Every recurring failure class becomes a durable regression test. | Not started |

## Why v0.5 stays open

v0.5's skill and its `amigos verify` command are built and tested, but the
milestone's exit criterion cannot be evaluated by the story that creates them:
`/implement` would have to exist before it could implement itself, and every
other story in the repository is already implemented.

**v0.6's first story is the demonstration.** This couples the two milestones'
timelines deliberately, on the v0.4 precedent that a milestone does not close on
code that was never exercised. The run must also be a fresh session — skills are
snapshotted at registration, so the session that writes a skill serves its
pre-edit text.

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
