# Intent

## User
Every agent and human making changes in a repository that has adopted
amigos-skills, and the maintainer who has to trust that the contract was
actually followed rather than remembered.

## Problem
The Definition of Ready is computable but nothing consults it. An agent can edit
any source file without a contract, and the only thing standing in the way is
whether it remembers the process. A rule that depends on voluntary recall is a
rule that disappears exactly when the project is under pressure, which is when
the contract matters most.

## Desired Outcome
A change to a governed file is refused unless a story is resolvable and that
story is ready. The refusal happens where the change is attempted, names the
story it looked for and the reason it refused, and cannot be satisfied by
anything the changing agent is able to write.

## Why Now
README section 32 places the gate before agent orchestration. Automating the
reasoning that produces contracts, while contracts remain optional, would
produce confident output nobody has to honour. The gate is what turns the
protocol from documentation into a constraint.

## In Scope
- Resolving the active story from the environment, a pointer file, or the
  branch name, in that order.
- Classifying a changed path as governed or exempt, governed by default.
- One command that decides whether a set of changed paths is permitted.
- A Claude Code hook that refuses an edit as it is attempted.
- A git pre-commit hook, and a command that installs it.
- Recomputing readiness from the contract files rather than trusting a
  committed verdict.

## Out of Scope
- Detecting that acceptance.feature was edited during implementation. That is
  contract immutability, and it belongs with the rest of strong enforcement.
- CI enforcement.
- Gating tool calls other than file edits.
- Any change to how readiness itself is computed.

## Success
Following the contract becomes easier than skipping it, and a maintainer reading
the repository can tell that the rule was enforced rather than observed.
