# Roadmaps

## Goal: v1.0 — self-hosting

> Amigos Skills develops Amigos Skills, with no privileged path around its own
> protocol.

See [versions/v1.0-self-hosting/](versions/v1.0-self-hosting/) and its
[milestones.md](versions/v1.0-self-hosting/milestones.md).

## Milestones

| Version | Scope | README phase | Status |
|---|---|---|---|
| v0.1 | Contract format and deterministic validator | 0 + 1 | Complete |
| v0.2 | Repository gate: no source change without a ready story | 2 | Complete |
| v0.3 | `/amigos` MVP, single orchestrator | 3 | Complete |
| v0.4 | Product, Development and QA as independent subagents | 4 | Not started |
| v0.5 | `/implement` | 5 | Not started |
| v0.6 | Strong self-hosting enforcement | 6 | Not started |
| v0.7 | Dogfooding failure corpus and evals | 7 | Not started |

Phase 8 (contract change workflow) and phase 9 (external integrations) follow
v1.0 and are not yet scheduled into milestones.

## Ordering principle

From README section 32:

> First make the rule explicit. Then make it checkable. Then make it hard to
> bypass. Only then automate the reasoning around it.

This is why the validator precedes the gate, and the gate precedes `/amigos`.
