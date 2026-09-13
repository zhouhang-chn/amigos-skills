# Documentation Map

## Durable docs

| Doc | Purpose |
|---|---|
| [project-overview.md](project-overview.md) | What the project is and how its pieces fit together. |
| [development-workflow.md](development-workflow.md) | How work is planned, executed and closed out. |
| [roadmaps.md](roadmaps.md) | Stable index of goals and milestones. |
| [component-design/contract-protocol.md](component-design/contract-protocol.md) | The `.amigos/` on-disk protocol. Platform-independent. |
| [component-design/validator.md](component-design/validator.md) | The deterministic Definition of Ready: checks, rules, exit codes. |
| [component-design/gate.md](component-design/gate.md) | The repository gate: what it governs, how it resolves a story, what it cannot do. |
| [component-design/orchestration.md](component-design/orchestration.md) | The `/amigos` skill: phases, bounds, and what a skill may never do. |

The root [README.md](../README.md) is the product thesis and the specification
of intent. These docs record how the thesis is being built.

## Execution docs

Execution docs live under [versions/](versions/), never directly under `docs/`.

| Folder | Scope |
|---|---|
| [versions/v1.0-self-hosting/](versions/v1.0-self-hosting/) | The goal: Amigos Skills develops Amigos Skills. |
| [versions/v0.1-deterministic-contract-core/](versions/v0.1-deterministic-contract-core/) | Milestone 1: the contract format and the deterministic validator. |
| [versions/v0.2-repository-gate/](versions/v0.2-repository-gate/) | Milestone 2: enforcement, so the contract stops being advisory. |
| [versions/v0.3-amigos-mvp/](versions/v0.3-amigos-mvp/) | Milestone 3: `/amigos`, so contracts are generated rather than hand-authored. |
| [versions/v0.4-independent-subagents/](versions/v0.4-independent-subagents/) | Milestone 4: three roles drafting blind, and the count that decides whether the split earns its cost. |

## Two planning surfaces, one boundary

The repository carries planning artifacts in two places and they do not overlap:

- `.amigos/stories/<id>/` holds **the product's acceptance contracts**: what a
  change must achieve and how success is judged. This is the artifact the
  framework itself produces, and it is read by every downstream agent.
  `.amigos/runs/` sits beside it and holds evidence about how a contract was
  produced — read by people, not by agents.
- `docs/versions/<version>/` holds **how the framework gets built**: gap
  analysis, design, ordered tasks, implementation notes.

Each milestone's `action-plan.md` names the story IDs it covers. A story states
the contract; the milestone states the plan for satisfying it.
