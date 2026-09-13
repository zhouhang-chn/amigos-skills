# Constraints

## Technical Constraints
- Vocabulary matching is case-insensitive and bounded to whole words, so
  "incorrect" inside a longer word does not fire on "correct".
- Only Then steps and the And or But steps that follow a Then are scanned for
  vocabulary.
- The rule set has one implementation, used both by the standalone command and
  by the readiness check.
- The default vocabulary is the list published in README section 17.
- No per-line suppression mechanism ships in this milestone.

## Dependencies
- STORY-001 defines acceptance.feature and .amigos/config.json.
- STORY-002 consumes these findings for the assertions_are_determinable check.

## Invariants
- Every finding carries a rule name, a file, a line number and a message.
- A repository may extend or shorten the vocabulary through .amigos/config.json,
  and may not disable the rule set.
- Findings are emitted in ascending line order.

## Relevant Components
- src/amigos/lint.py
- src/amigos/gherkin.py
- src/amigos/data/vague_words.txt
- scripts/lint_acceptance.py
