# Open Questions

## Blocking

None.

## Non-blocking

- Can partial work survive a contract conflict? Declaring `contract_change`
  withholds readiness, after which the gate refuses to commit the implementation
  already in the working tree. This contract has the skill declare it last, after
  reporting, and leave the tree uncommitted. Whether a conflicted story needs a
  way to save work in progress is a question for v0.6, which owns enforcement.
- README section 14 tells `/implement` to read `dor.json` for `"ready": true`,
  which contradicts `docs/component-design/gate.md`. This contract follows the
  gate. The README text should be corrected, but it is documentation and does not
  block implementation.
- Should `.amigos/config.json` carry a test command? Without one, "run tests"
  resolves by convention here and to nothing in a downstream repository. Adding
  the key is a protocol schema change and was put out of scope for this slice.
- What basis should scope expansion be judged against as the system grows? This
  contract uses the scenarios and the constraints' Relevant Components. A
  semantic comparison against `intent.md` may prove more accurate and is not
  attempted here.
- Writes made through `Bash` bypass the gate. `/implement` is the first skill
  that needs `Bash`, so the hole `docs/component-design/gate.md` defers "to be
  decided on evidence" now has its first consumer.
- `tests/test_dogfooding.py` enumerates story ids as a literal tuple that omits
  STORY-006, so closing this milestone edits a governed test file as a side
  effect. Whether that list should be derived rather than enumerated is
  unresolved.
