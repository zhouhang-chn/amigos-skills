# Intent

## User
The coding agent asked to build a story that already has a ready contract, and
the maintainer who has to be able to tell afterwards that the code was written
to satisfy the contract rather than the contract edited to match the code.
Immediately that user is this project: every milestone from here is meant to be
built through this skill.

## Problem
The project can produce a contract and refuse source changes without one, and
then the contract stops being consulted. Nothing carries it into the work: an
agent reads it once, implements from memory and chat, writes whatever tests
occur to it, and decides for itself when it is done.

Two failures follow from that one gap. Tests come to validate the implementation
instead of the intent, which is the outcome README section 1 exists to prevent.
And when a test derived from an acceptance criterion fails, the cheapest repair
available to the agent is to edit the criterion — `.amigos/**` is exempt from the
gate, so nothing stands in the way.

Until the execution side exists, the gate's achievement is only that work waited
for a contract, never that the work matched one.

## Desired Outcome
`/implement STORY-N` re-evaluates that story's readiness from the contract files
themselves, refuses to change governed code unless the story is ready at the
moment it is asked, and then works from the contract as its specification: the
acceptance scenarios' `Then` clauses become tests, the minimum behaviour those
tests require gets written, the suite is run, and the change is reported against
the scope the contract drew.

Anything that does not line up is reported rather than absorbed into the code: a
`Then` clause no test can observe is named instead of skipped, a changed file no
scenario or constraint calls for is listed as scope expansion, and a contract
that implementation proves wrong sends the story to `contract_change` and stops
for a human. A run leaves evidence a reviewer can inspect, including proof that
the four contract files are byte-identical to the versions that were ready.

## Why Now
The gate has been live since v0.2, so every governed change already costs a
contract, and the return on that cost only arrives when the contract also drives
the implementation. v0.6's enforcement — contract immutability above all — has
nothing to enforce against until an execution path exists: "the implementer must
not rewrite the criteria" cannot be mechanised before there is an implementer.
Section 32's ordering puts this last among the reasoning steps, after the rule
was made explicit, checkable and hard to bypass.

## In Scope
- A skill, invoked with a story id, that recomputes readiness from the contract
  files and refuses to change governed code unless the story is ready.
- Loading the four contract files as the working specification for the change.
- Turning the acceptance scenarios' `Then` clauses into executable tests, and
  naming the clauses it could not turn into tests rather than passing over them.
- Requiring a test for absent behaviour to fail before the source changes.
- Implementing the behaviour those tests require and no more.
- Running the repository's test suite and reporting the outcome.
- Reporting every changed governed file against the scenario or constraint it
  serves, and listing under scope expansion any that serves neither.
- A deterministic command that re-evaluates readiness and compares the four
  contract files against the hashes `dor.json` recorded, so "the requirement was
  not redefined" is a check rather than a claim.
- Declaring `contract_change` and stopping when implementation proves the
  contract wrong.
- A durable run record outside the story directory.

## Out of Scope
- Mechanical prevention of contract edits. README Phase 6 owns it and STORY-007
  already excluded it from the gate. Here the rule is stated by the skill and its
  violation is made visible by the hash comparison, not made impossible.
- Running or generating evals, golden tasks and graders. No eval harness exists
  in this repository; README places eval export at Phase 7 / STORY-008, so
  responsibility 5 narrows to running tests.
- A configured test command in `.amigos/config.json`. Downstream repositories
  have no declared test command and this milestone does not add one to the
  protocol schema; the skill uses the repository's documented command.
- Any change to a Definition of Ready check, a lint rule, a threshold, or the
  gate's decision. This milestone consumes readiness; it does not redefine it.
- Editing the acceptance criteria of any story, which is the prohibition the
  skill exists to hold.
- Adding a lifecycle state meaning "implemented". The declared states are fixed
  at `draft`, `amigos_running` and `contract_change`; adding one is a change to
  the state schema and the validator.
- `/implement` invoking `/amigos` itself on a contract conflict. One session
  must not both discover a conflict and author the criterion that replaces it.
- Autonomous commits, branch creation, pull requests and release steps.
- Demonstrating the milestone by running `/implement` on this story. The skill
  cannot build itself; v0.6's first story is the demonstration, and v0.5 stays
  open until that run produces evidence.
- The Codex mirror of the skill, deferred by README section 21 until the core
  loop works.

## Success
A reviewer can open the repository after a run and see that the code came from
the contract: tests that name the scenarios they judge, a contract whose hashes
match the versions that were ready, scenarios no test could observe named rather
than omitted, and every disagreement between contract and code recorded as a
contract change instead of resolved by editing the criteria.
