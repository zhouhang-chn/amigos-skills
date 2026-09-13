# Constraints

## Technical Constraints
- No agent's prompt may contain another agent's output during drafting.
  Independence that exists only in the instructions is not independence.
- The three drafting agents receive the same ticket and the same repository
  access, so a difference in their findings is a difference in perspective
  rather than in information.
- A findings record is structured, not prose: role, target file, target section
  and risk dimension, so overlap is computed rather than judged.
- The reconciliation pass writes the four contract input files and nothing else.
- Everything the v0.3 skill may not do still holds: no writing dor.json, no
  declaring ready or blocked, no inventing an assumption to clear a blocker, no
  commentary file in the story directory.
- The interview and repair loops keep their existing bounds.

## Dependencies
- STORY-004 supplies the orchestration this milestone splits.
- STORY-002 supplies the readiness evaluation the repair loop still consults.

## Invariants
- A drafting agent that returns no findings record stops the run rather than
  producing a contract from the remaining two.
- Conflicts between roles resolve into the contract, never into a separate
  commentary artifact.
- The contract files remain the only output of a run.
- The count of findings named by exactly one role is recorded for every run,
  including when it is zero.

## Relevant Components
- agents/product.md
- agents/dev.md
- agents/qa.md
- skills/amigos/SKILL.md
- .claude-plugin/plugin.json
