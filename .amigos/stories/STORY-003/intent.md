# Intent

## User
The QA perspective inside the Three Amigos gate, every reviewer reading an
acceptance contract, and every agent later turning Then clauses into tests.

## Problem
Given-When-Then only constrains behaviour if the Then clause can be judged the
same way by two independent readers. "Then the result is handled correctly"
looks like an assertion and asserts nothing. Scenarios with no Then at all, or
with no declared role in the contract, are equally unjudgeable. Left to model
judgement, these defects are argued about rather than detected.

## Desired Outcome
A command reads acceptance.feature and reports every clause that cannot be
independently judged, naming the file, the line and the rule that fired. The
same rules run inside the Definition of Ready check, so a contract cannot become
ready while carrying an empty assertion.

## Why Now
The counterexample and primary-path counts are meaningless if the scenarios they
count contain assertions nobody can evaluate. Linting has to exist before the
readiness check that consumes it can mean anything.

## In Scope
- Rejecting vague assertion vocabulary in Then-side steps.
- Rejecting a scenario that declares no Then step.
- Rejecting a step whose text is empty.
- Rejecting a scenario tagged neither @primary nor @counterexample, or tagged
  both.
- Warning when a Then step precedes the first When step.
- A repository-tunable vocabulary list.
- Human-readable and JSON output of the findings.

## Out of Scope
- Judging whether a scenario covers a worthwhile risk. That stays a human and
  Three Amigos decision.
- Rewriting a rejected clause into an acceptable one.
- Scanning Given or When steps for vocabulary. Those describe setup, not
  assertions.
- A per-line suppression comment. Withheld deliberately until a rule is shown
  to be wrong.

## Success
An empty assertion is caught by a tool the moment it is written, and the report
points at the exact line, so the fix is obvious and the argument does not happen.
