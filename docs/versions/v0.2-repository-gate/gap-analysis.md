# v0.2 Repository Gate — Gap Analysis

## Current state

v0.1 can decide readiness deterministically. Nothing consults that decision.
`amigos check` has to be run by someone who chooses to run it, which makes the
whole protocol advisory — precisely the property README section 18 rejects:

> The system must not depend on an agent voluntarily remembering the process.

## Gaps

| Gap | Severity | Impact |
|---|---|---|
| Source files can be changed with no ready story | High | The contract is a suggestion; it will be skipped first under time pressure. |
| No notion of which story a change belongs to | High | Even a willing agent has no way to say what it is working on, so nothing can be checked. |
| No definition of which files the contract governs | High | Without one, either everything is gated (including the contract itself, a deadlock) or nothing is. |
| Readiness is consulted only by a human-run command | Medium | Feedback arrives when someone thinks to ask, not when the violation happens. |
| `dor.json` can be stale relative to the contract files | Medium | A gate reading a committed verdict could be reading a verdict about different content. |

## Non-goals for this milestone

- Contract immutability enforcement: detecting that `acceptance.feature` was
  edited during implementation. `contract_hash` exists as the baseline, but the
  diffing belongs to v0.6 alongside the rest of strong enforcement.
- CI enforcement. The local loop has to be usable before it is made unbypassable.
- Any agent orchestration. `/amigos` is v0.3.

## Open questions

None blocking. The three kickoff questions are settled in
[design.md](design.md): branch-name resolution with explicit fallbacks, a
`gate` command with two thin adapters, and a fail-closed protected set.

Carried forward: whether the Claude Code hook should also gate `Bash` tool calls
that write files. Deferred until the Edit and Write path is proven.
