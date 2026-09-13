# Constraints

## Technical Constraints
- The skill never writes dor.json. Readiness stays derived.
- The skill never declares ready or blocked in state.json; it declares
  amigos_running while working and returns the story to draft when done.
- The repair loop is bounded. After a fixed number of attempts the story is left
  with its findings recorded rather than retried indefinitely.
- The interview is bounded to two rounds, so a missing answer ends as a recorded
  blocking question rather than an interrogation.
- The contract files are the output. The conversation that produced them is not
  an artifact and is not written anywhere.

## Dependencies
- STORY-001 supplies the contract format and scaffolding.
- STORY-002 supplies the readiness evaluation the repair loop reads.
- STORY-003 supplies the findings the repair loop acts on.

## Invariants
- A story the skill leaves behind is either ready, or blocked with at least one
  blocking question naming what stopped it.
- Every scenario the skill writes carries exactly one role tag.
- A question the skill could not answer appears in open-questions.md rather than
  as an assumption in intent.md.
- Reopening an existing story preserves its lifecycle history.

## Relevant Components
- skills/amigos/SKILL.md
- src/amigos/story.py
- src/amigos/cli.py
- .claude-plugin/plugin.json
