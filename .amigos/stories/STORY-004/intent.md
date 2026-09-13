# Intent

## User
A developer or coding agent holding a ticket and needing a contract before
implementation can begin, and the reviewer who has to decide whether the
resulting contract is worth trusting.

## Problem
Every contract in this repository was written by hand. Writing one well takes
three perspectives, a working knowledge of what makes an assertion judgeable,
and several rounds against a validator — which is exactly the work the project
promises to take off people. Until an agent can produce a contract that passes a
gate it did not write, the project demonstrates a file format rather than a
capability.

## Desired Outcome
A single command turns a story id and a description into a contract that passes
the Definition of Ready, or into a story that is explicitly blocked with the
questions that stopped it. The three perspectives are taken in sequence and then
challenged, so the output reflects more than one reading of the request. What
the command cannot determine, it asks about once; what remains unresolved it
records rather than invents.

## Why Now
The gate exists and refuses work without a ready story, so the cost of authoring
contracts is now paid on every change. Automating the reasoning is worth doing
only after the rule it serves is both explicit and enforced, which it now is.

## In Scope
- A skill that creates or reopens a story and drives it to a decided state.
- Three drafting phases matching the Product, Development and QA perspectives.
- One challenge pass in which each perspective attacks the others' output.
- A bounded interview when information is missing, before recording blockers.
- A bounded repair loop against the validator's findings.
- A command that records a lifecycle state transition in state.json.

## Out of Scope
- Independent subagents per perspective. One orchestrating model here; the
  split is the next milestone, which needs this as its baseline.
- Consuming a contract to write code.
- Contract diffing and reapproval.
- Reading tickets from an external tracker.

## Success
A reviewer reading a generated contract spends their time on scope and risk
rather than on rewriting sections, and the generated contract passes the same
validator that every hand-authored one passes.
