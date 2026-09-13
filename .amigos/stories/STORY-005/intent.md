# Intent

## User
Whoever decides whether the multi-agent design survives, and every reviewer who
has to trust that a generated contract reflects more than one reading of the
request.

## Problem
The contract is drafted by one model writing three sections in sequence. A
single model asked to take three perspectives in turn tends to produce three
restatements of one interpretation, because each section anchors on the last.
The output then carries the appearance of three perspectives without the
substance, which is worse than one perspective honestly labelled: it manufactures
confidence that nobody checked.

Nothing so far tests whether genuinely independent role agents find different
things, so the multi-agent design rests on argument rather than evidence.

## Desired Outcome
Product, Development and QA are drafted by separately invoked agents that cannot
see each other's work, and a reconciliation pass merges them. Each role's
findings are recorded separately and structured enough that overlap between
roles can be counted, so the question of whether the split earns its cost has a
number attached rather than an opinion.

## Why Now
v0.3 established the single-model baseline this milestone has to beat. README
section 32 attaches a kill criterion to this phase — the multi-agent design does
not survive if it only produces duplicated prose — and a kill criterion that
cannot be evaluated is not one.

## In Scope
- Agent definitions for the Product, Development and QA perspectives.
- Blind drafting: all three see the ticket and the repository, none sees another
  agent's output.
- A reconciliation pass that merges the three drafts and surfaces conflicts.
- A structured findings record per role, carrying role, target file, target
  section and risk dimension.
- Counting which findings are named by one role only.

## Out of Scope
- Consuming a contract to write code.
- The eval corpus and graders.
- A fourth Designer perspective.
- Changing any Definition of Ready check, threshold or lint rule.
- A bounded challenge round between drafting and reconciliation. Considered and
  deferred: it is three further agent invocations per run, and blind drafting
  plus reconciliation is enough to answer whether independence changes anything.

## Success
The project can say, with a count rather than an impression, whether three
independent agents find things one model in three passes does not — and is
willing to act on the answer in either direction.
