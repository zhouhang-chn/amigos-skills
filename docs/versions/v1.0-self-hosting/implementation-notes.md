# v1.0 Self-Hosting — Implementation Notes

Goal-level notes. Milestone detail lives in each milestone folder.

## v0.1 — complete

Delivered the contract format and the deterministic validator. Full detail in
[../v0.1-deterministic-contract-core/implementation-notes.md](../v0.1-deterministic-contract-core/implementation-notes.md).

Decisions promoted to durable docs:

- The `state.json` / `dor.json` split, and the rule that a declared state can
  only withhold readiness — now in
  [contract-protocol.md](../../component-design/contract-protocol.md).
- The structural-versus-failing distinction and its exit codes — now in
  [validator.md](../../component-design/validator.md).

## v0.2 — complete

Delivered the repository gate. Full detail in
[../v0.2-repository-gate/implementation-notes.md](../v0.2-repository-gate/implementation-notes.md).

Decisions promoted to durable docs:

- The gate's structure, resolution order, fail-closed governance and its three
  known holes — now in [gate.md](../../component-design/gate.md).

The project is now subject to its own gate: from here, work on Amigos Skills
needs a ready story on a branch that resolves it.
