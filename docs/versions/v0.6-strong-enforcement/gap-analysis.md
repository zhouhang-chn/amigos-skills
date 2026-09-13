# v0.6 Strong Self-Hosting Enforcement — Gap Analysis

Milestone exit criterion: *no privileged development path around the protocol.*

README section 32, phase 6 names four protections to add:

```text
modifying acceptance.feature during implementation
working against blocked stories
changing business code without an active story
silently changing contract state
```

## Current state

| Piece | Since | What it enforces |
|---|---|---|
| `amigos check` | v0.1 | Derives readiness from the contract files. Writes `dor.json`, including a sha256 of each input under `contract_hash`. |
| `amigos gate` | v0.2 | Refuses a changed governed path unless a resolvable story is ready. Fail-closed: governed unless exempt. |
| PreToolUse hook | v0.2 | Refuses `Edit`, `Write` and `NotebookEdit` as they are attempted. |
| pre-commit hook | v0.2 | Refuses a commit whose staged set is refused. |
| `amigos state` | v0.1 | Refuses to declare `ready` or `blocked`; both are derived. |
| `amigos verify` | v0.5 | Re-derives readiness and diffs the four contract files against `dor.json.contract_hash`. |
| `skills/implement/SKILL.md` | v0.5 | States six prohibitions that hold by instruction, not by mechanism. |
| `tests/test_dogfooding.py` | v0.2 | This repository's own stories held to the gate they impose on others. |

Phase 6's third bullet — *changing business code without an active story* — is
substantially done. v0.2 built it. What v0.6 owes it is enforcement that does not
live inside the process it constrains.

The other three bullets have nothing behind them.

## Gaps

| # | Gap | Severity | Impact |
|---|---|---|---|
| 1 | `verify`'s baseline is `dor.json.contract_hash`, and `amigos check` rewrites that field on every run. | High | An agent that edits `acceptance.feature` and re-runs `check` passes verification. The one command that answers "was the requirement redefined" can be silenced by the agent it questions. |
| 2 | Nothing refuses an edit to the contract of a story that is already ready. `.amigos/**` is exempt from the gate unconditionally. | High | Phase 6's first bullet has no mechanism at all. The rule exists only as a line in `skills/implement/SKILL.md`, which is the arrangement README section 18 exists to reject. |
| 3 | There is no CI. The repository has no `.github/`, no pipeline, no check that runs outside a developer's checkout. | High | Every enforcement point sits inside the blast radius of the agent it enforces. |
| 4 | `git commit --no-verify` skips the pre-commit hook. | High | Named in `gate.md` as tolerated in v0.2 and closed by v0.6. Still open. |
| 5 | `.claude/settings.json` is governed, but a ready story permits editing it — including to remove the hook that is doing the gating. | High | Under any ready story the in-session gate can disable itself, and the pre-commit hook is the only thing left. |
| 6 | The PreToolUse matcher is `Edit\|Write\|NotebookEdit`. Writes made through `Bash` are not gated. | High | Deferred in v0.2 pending evidence. The evidence has arrived — see below. |
| 7 | Declaring `contract_change` withholds readiness immediately, so the gate then refuses to commit the partial implementation already in the tree. | Medium | `/implement`'s conflict path works only because the skill orders its steps carefully. A mechanism that depends on doing things in the right order is the thing this milestone is replacing. |
| 8 | Nothing detects a hand-edited `state.json`. `amigos state` refuses to declare `ready` or `blocked`, but editing the file directly bypasses the command. | Medium | Phase 6's fourth bullet. A `declared_state` with no supporting history entry is invisible. `dor.json` is safe here by construction — every consumer re-derives it — so the gap is `state.json` alone. |
| 9 | `tests/test_dogfooding.py` enumerates story ids in a literal tuple, and still omits STORY-006. | Low | The self-hosting invariant is tested through an allowlist, so it stops covering each new story until somebody remembers. That is precisely the erosion the gate's fail-closed design refuses to accept, running unchecked inside the test that asserts the invariant. |
| 10 | `amigos check` writes `dor.json` on every invocation, `generated_at` included. | Low | A command that reads like an inspection dirties the tree, and it is the mechanism behind gap 1. Observed during this milestone's kickoff: running `check` to verify a commit left `dor.json` modified. |

## The Bash hole now has evidence

v0.2 recorded gating `Bash` writes as a non-blocking open question, to be decided
once the `Edit`/`Write` path had been used enough to show whether the hole
mattered. Two things have since decided it.

`/implement` needs `Bash` to run a test suite, so the first skill that must use
the tool is also the skill doing the governed writing.

And the session that kicked off this milestone ran under instructions to prefer
`Bash` for file edits. Every file it wrote went through `sed`, `cat` and
heredocs. The PreToolUse hook did not fire once. The hole is not hypothetical and
it is not rare: it is what happens when an ordinary configuration meets an
ordinary agent.

## What the exit criterion does and does not claim

> The project has no privileged development path around its own protocol.

This is a claim about *privilege*, not about impossibility. A maintainer with
push access and administrative rights can always merge anything; no repository
mechanism survives its own administrator. What the criterion forbids is a route
that exists **for this project and not for the projects it asks to adopt it** —
an exemption in the config, a skip in the test suite, a rule the framework
applies to others and suspends for itself.

Stating this now, before the work, so the milestone is not later marked complete
against a criterion quietly re-read as "bypass is impossible", and not left open
forever against one that no software can satisfy.

## Non-goals

- **The contract change workflow.** Contract diffs and explicit reapproval are
  phase 8. v0.6 refuses and detects contract edits; it does not build the
  ceremony for making one legitimately.
- **Evals, golden tasks and graders.** Phase 7, v0.7.
- **External integrations.** Phase 9.
- **A new lifecycle state meaning "implemented".** Deferred in v0.5 and still a
  schema change nothing yet requires.
- **Making bypass impossible.** See above.

## Open questions

- **Which commit is the contract's baseline** when the contract and its
  implementation share a branch? The merge-base with the integration branch is
  the obvious answer and it degenerates to HEAD on the integration branch itself.
- **Can partial work survive a contract conflict?** Carried unanswered from v0.5.
  Gap 7 is the same question wearing the enforcement mechanism's clothes.
- **Is gating `Bash` a matter of parsing commands, or of checking the tree after
  the fact?** Parsing a shell command to predict what it writes is a losing game;
  a PostToolUse check that catches the write after it lands refuses later but
  refuses reliably.
- **Which CI host.** The repository names none, and a workflow file written for
  the wrong one is a file that never runs.
