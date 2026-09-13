# Constraints

## Technical Constraints
- The validator is the only writer of dor.json.
- The check names in dor.json match the names published in README section 5.
- The validator runs on the Python standard library, so it works in any
  repository without an install step.
- A declared state of amigos_running or contract_change prevents readiness
  regardless of the checks.
- Structural defects must not produce a derived dor.json. Refusing to write is
  preferred over recording a judgement about a malformed input.

## Dependencies
- STORY-001 defines the contract format this story reads.
- STORY-003 supplies the acceptance lint consumed by the
  assertions_are_determinable check.

## Invariants
- Two runs over unchanged contract files produce the same checks, the same
  failures and the same exit code.
- dor.json validates against schemas/dor.schema.json every time it is written.
- No value present in state.json can set ready to true.

## Relevant Components
- src/amigos/dor.py
- src/amigos/gherkin.py
- src/amigos/story.py
- scripts/check_dor.py
- schemas/dor.schema.json
