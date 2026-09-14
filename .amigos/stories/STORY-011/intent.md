# Intent

## User

The maintainer or reviewer of a repository that has adopted Amigos Skills, and
the agent working inside it. Since STORY-010, `state.json` decides whether a
finished contract may be edited: a story that is ready has its four contract
input files frozen, and the documented way to reopen them is to declare
`contract_change`. That declaration is a line of JSON no mechanism has ever
looked at twice.

Two readers, at two moments, and this story owes both:

- the worker at the keyboard, who should be stopped while the change is still in
  front of them;
- the reviewer reading the repository afterwards, for whom a `declared_state`
  with no supporting history entry is today indistinguishable from one the
  protocol produced.

Immediately that user is this project. Nine of its ten stories are ready, every
one of them frozen by STORY-010, and every freeze lifts to a word written into a
file the gate reads live and never questions.

## Problem

Two of README section 32 phase 6's four named protections have no mechanism, and
they meet in the same file.

**Contract state changes without leaving evidence.** `amigos state` refuses
`ready` and `blocked` from the writing end and `read_state()` refuses them from
the reading end, but a hand edit takes neither path. Writing
`"declared_state": "contract_change"` into `state.json` with a text editor
produces a story that is not ready, which lifts STORY-010's freeze and makes a
ready story's `acceptance.feature` editable again — with no history entry, no
note, and nothing comparing the declaration against the trail meant to support
it. The same edit runs the other way too: `draft` written over `amigos_running`
mid-run lets a half-written contract read as ready. And because `set_state()` is
the only writer that appends, a hand edit can replace the `history` array
outright; the docstring calling a contract's lifecycle *evidence* is the only
thing that says it should not.

The gap was filed at Medium while `state.json` withheld readiness and little
else. STORY-010 made it load-bearing, and recorded the consequence rather than
hiding it: the freeze fails open, so a `state.json` that cannot be evaluated
unlocks a contract, and a hand-written `contract_change` unlocks it just as
cheaply.

**A blocked story is refused only incidentally.** `blocked` is derived — it is
what a story is when nothing withholds it and a check fails — and today a blocked
story draws the same refusal as a story with no contract at all. That refusal
ends `Make the story ready, then retry: amigos check <id>`, naming a command that
cannot make a blocked story ready: re-running the validator against a failing
contract returns the same verdict. STORY-010 had to correct exactly this shape of
guidance once already. Meanwhile the rule itself — *stop before touching any
governed file* — is prose in `skills/implement/SKILL.md`, which is the
arrangement README section 18 exists to reject.

## Desired Outcome

A declared state its own recorded lifecycle does not support stops being
invisible, and stops being a cheaper unlock than the sanctioned route.

The gate refuses every governed write for a story whose lifecycle record is
inconsistent, at both adapters, so the worker meets the refusal at a moment they
cannot decline to pass through. The refusal names the story, names `state.json`,
and is distinguishable from the verdicts already in the vocabulary — not ready,
not verified, and not the frozen-contract refusal STORY-010 added.

`amigos state <STORY-ID>` with no transition reports whether that story's
lifecycle record holds together, so a reviewer can ask the question directly
rather than inferring it from a refusal.

A blocked story draws a refusal that says `blocked`, names a Definition of Ready
check that failed, and names re-contracting through the amigos skill as the route
out — because a blocked story is a different job, not a smaller one.

The record stays repairable. A write to a story's own `state.json` is permitted
even while that record is inconsistent, so a damaged file can be fixed rather
than deadlocking the repository that holds it.

Readiness stays derived. Nothing here lets a declaration grant readiness, adds a
state an agent may declare, or changes what the seven checks mean. The refusal is
a gate decision and not a readiness verdict, so STORY-010's fail-open rule stays
exactly as it shipped.

## Why Now

This is v0.6 milestone task 5, gap 8 of its gap analysis, and phase 6's second
and fourth bullets. It follows STORY-010 because STORY-010 is what made it
urgent: before that story `state.json` only withheld readiness; after it, the
same file decides whether a finished contract can be rewritten. The protection
that shipped in STORY-010 rests on the gap this story closes, and STORY-010's own
`open-questions.md` and `docs/component-design/gate.md` both record that
dependency.

The milestone's exit criterion is *no privileged development path around the
protocol*. A route that lifts a contract freeze with a text editor and leaves no
trace is that path.

## In Scope

- A story's lifecycle record is inconsistent when `declared_state` differs from
  the `state` of the last `history` entry, or `updated_at` differs from that
  entry's `at`. This is what `set_state()` guarantees by construction, so every
  transition the command writes satisfies it.
- A story's lifecycle record is also inconsistent when the committed `history` is
  not a prefix of the working tree's `history`, so an entry deleted or rewritten
  after it was committed is caught rather than laundered.
- The gate refuses every governed write for a story whose record is inconsistent,
  at the PreToolUse adapter and at the pre-commit adapter alike.
- The story judged is the one the gate already resolves for source paths, and the
  story a contract path names for contract paths — the two origins STORY-010
  established.
- A write to a story's own `state.json` is permitted while that story's record is
  inconsistent, so the record can be repaired.
- A `state.json` that cannot be parsed is refused rather than permitted, because
  an unreadable record must not be a cheaper unlock than a readable one.
- A question git cannot answer — no repository, or a `state.json` never committed
  — is reported as unanswered and does not by itself produce a refusal.
- `amigos state <STORY-ID>` with no `--set` reports that story's lifecycle record
  and whether it holds together, and writes nothing.
- A refusal against a blocked story names `blocked`, names a failed Definition of
  Ready check, and names re-contracting through the amigos skill.
- Readiness derivation, the seven checks, the declarable-state list, and the
  meaning of `ready` and `blocked` are unchanged. `state.json` stays outside
  `HASHED_FILES` and outside what `amigos verify` compares.
- The legitimate paths keep running without added ceremony: `amigos create`, the
  amigos skill's Phase 0 and Phase 7, and the implement skill's conflict path.
- This repository is held to the rule it ships: its ten stories, and its closeout
  commands, pass under the new rule rather than around it.
- The rule and its limits recorded in `docs/component-design/gate.md`.

## Out of Scope

- **Detecting hand authorship.** A hand edit that appends a well-formed entry and
  updates `declared_state` and `updated_at` is byte-identical to what
  `amigos state` writes; there is no key, no signature and no writer identity to
  compare. This story detects an *unrecorded* change, which is what gap 8's own
  wording names. Saying otherwise would promise a mechanism nothing here builds.
- **Making bypass impossible.** A maintainer with administrative rights can merge
  anything, and a careful enough forgery satisfies whatever is compared. What is
  removed is a route that exists for this project and not for the projects it
  asks to adopt it.
- Milestone tasks 3 and 4 — CI over a push range, and governed writes made
  through `Bash`. Each needs its own contract. This story is in-session only.
- Gaps 4, 5, 7, 9 and 10: `git commit --no-verify`, `.claude/settings.json`
  editable under a ready story, partial work across a contract conflict, the
  dogfooding story-id allowlist, and `amigos check` rewriting `dor.json`.
- Tamper detection for `dor.json`. Every consumer re-derives it and none treats
  it as authority, which the gap analysis records as safe by construction.
- `.amigos/ACTIVE` and `.amigos/config.json`. Both change the gate's verdict
  without touching a contract file and neither is named by gap 8; they are
  siblings of gap 5 and are recorded as a non-blocking question.
- Adding a declarable state, removing one, or admitting `ready` or `blocked` into
  `state.json`. That refusal is load-bearing and this story does not touch it.
- Shipping `schemas/state.schema.json` validation inside `read_state()`. It is a
  real asymmetry — this repository holds itself to a check it does not ship — and
  it is recorded as a non-blocking question rather than widened into here.
- Requiring a `--note` on a transition. An unexplained reopening through the
  sanctioned command is a hole; it is a different hole from an unrecorded one.
- The phase 8 contract change workflow. Making an unrecorded reopening visible is
  not the same as building ceremony for a legitimate one.
- A configuration switch for the new refusal. An off switch this project must
  never flip is not something to ship to projects that inherit the rule.
- Retroactive judgement on this repository's committed history.
- Any change to how `amigos verify` derives its baseline, settled by STORY-009.

## Success

An agent that hand-writes `contract_change` into a ready story's `state.json` to
reach its `acceptance.feature` is refused, and told which story and which file
made the refusal — instead of being handed the edit.

An agent that starts work against a blocked story is told the story is blocked
and told where it goes next, instead of being sent to a command returning the
same verdict.

A damaged lifecycle record can still be repaired, and the protocol still runs
end to end: scaffold, draft, implement, reopen on a genuine conflict, close out.

This repository's ten stories pass the rule it now imposes on others, and phase
6's second and fourth bullets have mechanisms behind them rather than sentences.
