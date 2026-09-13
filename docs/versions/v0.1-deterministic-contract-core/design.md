# v0.1 Deterministic Contract Core — Design

## Resolutions to the gaps

| Gap | Resolution |
|---|---|
| `dor.json` ownership | Split into agent-owned `state.json` and validator-owned `dor.json`. |
| Non-derivable states | `declared_state` holds lifecycle events and can only ever withhold readiness. |
| Counterexample signal | Required `@primary` / `@counterexample` tags; neither or both is a structural error. |
| Immutability baseline | `dor.json.contract_hash` records SHA-256 of every input file from day one. |
| Vague assertions | A lint rule over assertion steps, shared by the standalone command and the DoR check. |

Full detail of the resulting protocol and validator is in
[contract-protocol.md](../../component-design/contract-protocol.md) and
[validator.md](../../component-design/validator.md). This document records the
choices; those record the contract.

## Structure

Logic lives in an importable package, `src/amigos/`, with `scripts/*.py` as thin
wrappers so both `python scripts/check_dor.py STORY-123` (README section 16) and
`amigos check STORY-123` (README section 22) work. `src/` layout avoids a
confusing `amigos/` next to `.amigos/` at the repository root.

## Tests

- Unit tests per module, including the parser's line accuracy and the lint's
  false-positive guards.
- `tests/fixtures/stories/`: eleven stories, each breaking exactly one rule, so
  a failure names its own cause.
- `tests/test_dogfooding.py`: this repository's own stories must pass the gate,
  and each committed `dor.json` must match a fresh evaluation.

## Alternatives rejected

- *A third-party Gherkin library.* Correct and complete, but it would add a
  runtime dependency to a tool whose value depends on running anywhere without
  an install step. A ~200-line parser over a declared subset is enough, provided
  unsupported constructs raise rather than being skipped.
- *A heuristic counterexample detector.* See the goal-level design.
- *Per-line lint suppression.* Withheld on purpose: README section 31 says to
  determine whether the rule is wrong before building the escape hatch.
