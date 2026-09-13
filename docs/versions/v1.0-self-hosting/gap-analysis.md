# v1.0 Self-Hosting — Gap Analysis

## Current state

The repository holds a complete specification of intent (`README.md`) and, as of
v0.1, the contract format and deterministic validator. There is no agent
orchestration, no enforcement, and no eval corpus.

## Gaps to the goal

| Gap | Severity | Impact |
|---|---|---|
| Nothing prevents a source change without a ready story | High | The protocol is advisory, so it will be skipped under time pressure. |
| Contracts are hand-authored | High | The framework cannot yet produce the artifact it exists to produce. |
| No implementation path from a ready contract | High | The contract stops at the boundary it was built to cross. |
| Role independence unproven | Medium | Three subagents may produce three paraphrases rather than three perspectives. |
| No failure corpus | Medium | Recurring failures cannot become regressions, so the flywheel never starts. |
| `acceptance.feature` can be edited during implementation | Medium | The contract is only immutable by convention. |
| Codex parity unbuilt | Low | The protocol claims platform independence without a second platform proving it. |

## Non-goals

PR review, a replacement for code review, an autonomous product manager, a
generic multi-agent discussion system, or a way for implementation agents to
approve their own requirements.

## Open questions

- Does role independence improve contract quality enough to justify three
  subagents? To be answered with v0.4 dogfooding evidence, not in advance.
- Should the repository gate resolve the active story from the branch name, a
  pointer file, or an explicit argument? Deferred to v0.2's design.
