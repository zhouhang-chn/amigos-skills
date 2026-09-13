# Intent

## User
A developer or coding agent adopting amigos-skills in a repository, and every
downstream agent that later reads a story contract.

## Problem
There is no defined on-disk format for a story contract. Without one, each agent
invents its own file names, section headings and readiness representation, so no
deterministic tool can judge a contract and no two repositories agree on what a
story even looks like.

## Desired Outcome
A repository has a single documented contract format: a fixed set of files per
story, a fixed set of section headings inside them, an agent-owned lifecycle
file, and a validator-owned readiness file. Scaffolding a new story produces
that exact file set, pre-filled with placeholders that cannot be mistaken for a
finished contract.

## Why Now
Every later capability depends on this shape. The validator, the repository
gate, the /amigos skill and the /implement skill all read these files. Changing
the format after those exist is far more expensive than defining it first.

## In Scope
- The five contract input files per story: intent.md, constraints.md,
  acceptance.feature, open-questions.md, state.json.
- The derived output file dor.json and its JSON Schema.
- The JSON Schema for state.json, restricting which lifecycle states an agent
  may declare.
- Templates for each input file.
- Story workspace scaffolding that writes the templates into a new story.
- Repository configuration at .amigos/config.json.

## Out of Scope
- Evaluating whether a contract is ready. That is STORY-002.
- Linting acceptance criteria. That is STORY-003.
- Generating contract content from a ticket. That is the /amigos skill.
- Any enforcement that blocks source edits.
- Synchronising story IDs with an external tracker.

## Success
A developer can scaffold a story, see exactly which files a contract needs, and
fill them in without consulting the README. An unedited scaffold is visibly
unfinished rather than silently acceptable.
