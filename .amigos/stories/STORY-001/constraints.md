# Constraints

## Technical Constraints
- The contract lives under .amigos/ and stays platform-independent: no file may
  depend on Claude Code or Codex specifics.
- Input files are hand-editable text. Markdown and Gherkin only, no generated
  markup.
- state.json accepts only the lifecycle states an agent is allowed to declare.
  The values ready and blocked are not among them.
- dor.json has exactly one writer, the validator. Scaffolding does not create it.
- Story scaffolding must never overwrite an existing story directory.

## Dependencies
- None. Scaffolding runs on the Python standard library.

## Invariants
- The five input file names are identical in every story and every repository.
- A scaffolded story that has not been edited must not satisfy the Definition of
  Ready.
- A story directory contains no files beyond the five inputs plus dor.json.

## Relevant Components
- templates/
- schemas/dor.schema.json
- schemas/state.schema.json
- src/amigos/story.py
- src/amigos/config.py
- scripts/create_story.py
