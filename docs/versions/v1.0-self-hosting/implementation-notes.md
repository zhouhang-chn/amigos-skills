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
