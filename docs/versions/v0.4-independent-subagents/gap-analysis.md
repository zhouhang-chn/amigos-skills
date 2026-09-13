# v0.4 Independent Subagents — Gap Analysis

Story: **STORY-005**, the first contract in this repository produced by running
`/amigos` rather than by hand. Committed ready in `ac5f549`.

## Current state

v0.3 ships a single orchestrating model that walks the Product, Development and
QA phases in sequence inside one context. It works: it produced STORY-005, and
that contract passed all seven Definition of Ready checks on the first attempt.

What it does not do is make the three perspectives independent. Phases 1, 2 and
3 run in one conversation, so Development reads Product's draft before writing
constraints and QA reads both before writing scenarios. Each phase anchors on
the last.

## Gaps

| Gap | Severity | Impact |
|---|---|---|
| The three perspectives share one context, so a later role inherits an earlier role's framing | High | Three restatements of one interpretation carry the appearance of three perspectives without the substance. That is worse than one perspective honestly labelled: it manufactures confidence nobody checked. |
| Nothing measures whether the split changes the output | High | README section 32 attaches a kill criterion to this phase. A kill criterion nobody can evaluate is not one. The project cannot currently answer whether independence earns its cost. |
| No structured record of what each role found | Medium | Overlap between roles is currently a matter of impression. Impressions cannot be compared across runs and cannot kill a design. |
| The `/amigos` skill has never been invoked as a registered skill | Medium | v0.3 executed `SKILL.md` literally because the file was created during that session. Discovery and invocation are untested. |
| The repair loop has never run against a real validator rejection | Low | Its behaviour under failure is asserted by reading, not by evidence. |

## What the contract already settles

STORY-005 was drafted, challenged and interviewed in v0.3, so several design
questions arrive answered rather than open:

- **Blind drafting, then reconciliation.** No agent's prompt may contain another
  agent's output during drafting.
- **Structured findings, not prose.** Role, target file, target section, risk
  dimension — so overlap is computed rather than judged.
- **Overlap is counted, including when the count is zero.** A run in which the
  split adds nothing must say so rather than quietly pass.
- **A missing findings record stops the run.** Two roles plus a gap is not the
  Three Amigos.

## The measurement problem this milestone has to solve

The kill criterion is "do independent agents find things one model does not".
Turning that into a number introduces a failure mode the contract does not name:
**the count is only as honest as the comparison.**

Two roles that notice the same risk and describe it in different words produce
two findings that no key will match. That inflates the count of findings named
by exactly one role — and that is precisely the number that decides whether the
milestone survives. Free-text vocabulary biases the measurement toward the
answer the milestone wants to hear.

This is a gap in the measurement, not in the contract. STORY-005's non-blocking
open question defers a *fixed* dimension vocabulary until there are runs to
compare. It does not prevent giving the three agents the same *suggested*
vocabulary, which is what the design does and why.

## Non-goals

Named here so they stay out, from STORY-005's `## Out of Scope`:

- Consuming a contract to write code — that is v0.5.
- The eval corpus and graders — v0.7.
- A fourth Designer perspective — README section 34, still optional.
- Any change to a Definition of Ready check, threshold or lint rule. This
  milestone changes how a contract is drafted, not what makes it ready.
- A bounded challenge round between drafting and reconciliation. Considered and
  deferred in the contract with its reason: it is three further agent
  invocations per run, and blind drafting plus reconciliation is enough to
  answer whether independence changes anything.

## Open questions

- Whether the reconciliation pass should record the three drafts as well as the
  three findings records. The contract requires only the findings. Deferred:
  building the wider audit trail before knowing the narrow one is used is the
  escape hatch README section 31 warns about.
- Whether a risk dimension vocabulary should eventually be enforced rather than
  suggested. Carried forward from STORY-005 unchanged; it needs comparable runs
  to answer, and this milestone produces the first one.
