# Constraints

## Technical Constraints
- The gate recomputes readiness from the contract input files. A committed
  dor.json is a record, not an authority, and may be stale.
- The governed set is defined by exclusion: a path is governed unless it matches
  an exempt pattern, so a directory added tomorrow is governed today.
- The gate must run without git present, refusing rather than failing open when
  it cannot determine what changed.
- The decision is one command. The Claude Code hook and the pre-commit hook are
  adapters over it and hold no rules of their own.
- Installing the git hook must not destroy a pre-commit hook the repository
  already has.

## Dependencies
- STORY-002 supplies the readiness evaluation the gate consults.
- STORY-001 supplies the story workspace the gate resolves against.

## Invariants
- The contract files, the docs and repository metadata stay editable with no
  story, or the gate would prevent the work that makes a story ready.
- Nothing an implementing agent can write to a story directory changes the
  gate's decision from refuse to permit.
- A resolution that finds more than one candidate story refuses rather than
  choosing one.
- The exit code distinguishes a refusal from a gate that could not run.

## Relevant Components
- src/amigos/gate.py
- src/amigos/cli.py
- src/amigos/config.py
- integrations/claude-code/
- integrations/git/
