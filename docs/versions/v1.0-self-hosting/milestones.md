# v1.0 Self-Hosting — Milestones

| Version | Scope | Depends on | Exit criterion | Status |
|---|---|---|---|---|
| v0.1 | Contract format, deterministic validator, acceptance lint, scaffolding | — | Readiness can be rejected without asking a model. | Complete |
| v0.2 | Repository gate refusing source changes without a ready story | v0.1 | The project cannot casually bypass its own contract. | Complete |
| v0.3 | `/amigos` MVP, one orchestrator preserving the three logical phases | v0.2 | Amigos Skills can create usable contracts for its own development. | Complete |
| v0.4 | Product, Development and QA as independent subagents | v0.3 | The three agents discover different classes of ambiguity, scope risk and failure mode. | Not started |
| v0.5 | `/implement` | v0.4 | The project moves from a ready contract to verified implementation without redefining the requirement. | Not started |
| v0.6 | Strong self-hosting enforcement, contract immutability | v0.5 | No privileged development path around the protocol. | Not started |
| v0.7 | Dogfooding failure corpus and evals | v0.6 | Every recurring failure class becomes a durable regression test. | Not started |

## Notes on ordering

v0.2 precedes v0.3 deliberately. README section 32 places the repository gate
before agent orchestration: an unenforced rule is a suggestion, and automating
reasoning on top of a suggestion produces confident output nobody has to honour.

v0.4 carries a genuine kill criterion. If independent subagents only produce
duplicated prose, the multi-agent design does not survive the milestone.
