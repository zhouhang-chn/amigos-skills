# Intent

## User

The maintainer or reviewer of any repository that has adopted Amigos Skills, who
needs one thing to hold of a ready story: the criteria it will be judged against
cannot be quietly rewritten by the agent being judged.

Immediately that user is this project. Every story in this repository is ready,
and the only thing standing between a failing test and an edited `Then` clause is
an agent remembering a line of prose.

The gate cannot tell an implementing agent from a human maintainer, and this
story does not ask it to. The rule binds everyone working in a checkout with the
hooks installed.

## Problem

Nothing refuses the edit.

STORY-009 made a contract edit detectable: `amigos verify` derives its baseline
from git history, so the comparison can no longer be reset by re-running
`amigos check`. But detection answers a question only when somebody asks it, and
the agent with the strongest reason not to ask is the one that made the edit.

The rule itself lives in two places, both of them text: a row in
`skills/implement/SKILL.md` and a sentence in README section 19. That row says so
out loud — *`.amigos/**` is exempt from the gate, so nothing stops you; this is
the rule that has to hold without enforcement*. README section 18 exists to
reject that arrangement.

The exemption is not an oversight. `.amigos/**` is exempt because gating the
story directory would deadlock the protocol: a story can only become ready by
editing a story. The single sentence that keeps contract authoring possible is
the same sentence that leaves a finished contract unprotected, and the gate
cannot presently tell those two situations apart.

## Desired Outcome

A change to a contract input file of a story that is ready is refused, by the
gate, at both points where the gate is already installed: when an agent attempts
the write, and when the change is staged for commit.

Readiness is derived from **the contract as it stood before the change under
consideration** — the working tree at edit time, `HEAD` at commit time. Deriving
it from the edited content would permit the most damaging edits and refuse only
the harmless ones, because deleting a counterexample is itself an edit that makes
a story unready.

The refusal is legible and distinguishable from the gate's existing refusal for
an unready story. It names the story the changed path belongs to, names the file,
and names the route that is not a bypass: declare a state that withholds
readiness and re-contract through `/amigos`. That route exists today and this
story adds no ceremony to it.

Everything the protocol needs in order to keep working stays permitted:
`dor.json` and `state.json`, run records under `.amigos/runs/`, the contracts of
stories that are not ready, scaffolding a new story, and the commit that
publishes a contract for the first time.

## Why Now

This is README section 32 phase 6's first named protection, gap 2 of the v0.6
gap analysis at severity High, and task 2 of the milestone sequence. It is
sequenced after STORY-009 because a refusal is only worth having once the
baseline it protects cannot be moved from inside the session.

The milestone's exit criterion is *no privileged development path around the
protocol*. While this rule is prose, Amigos Skills asks downstream projects to
accept a mechanical gate and holds itself to an instruction — the asymmetry
README section 31 forbids.

## In Scope

- The gate refuses a change to `intent.md`, `constraints.md`,
  `acceptance.feature` or `open-questions.md` of a story that is ready.
- Readiness for this decision is derived from the contract before the change:
  the working tree at edit time, `HEAD` at commit time. It is recomputed on every
  call and never read from a committed `dor.json`.
- The refusal follows **the story the changed path names**, not the resolved
  active story, so editing another ready story's contract is refused too.
- The refusal holds at both installed adapters, because a rule that holds in only
  one is a rule with a documented way around it.
- A staged deletion or rename of a ready story's contract file is refused.
  `gate.staged_paths()` collects with `--diff-filter=ACMRT` today, which omits
  deletions, so a staged `git rm` of `acceptance.feature` currently reaches no
  decision at all.
- The declared state is read live from `state.json`, so `contract_change` (and
  `amigos_running`, which `/amigos` Phase 0 declares as a matter of course)
  reopens the contract without needing a separate commit first.
- Scaffolding a new story, and the commit that first records a contract, stay
  permitted while other stories are ready.
- The rule fails **open**, which is the opposite of the gate's default and is
  therefore stated rather than inferred: a path is refused only when the story
  that owns it demonstrably evaluates ready.
- This repository is held to the rule it ships. Its nine ready stories, its
  closeout commits, and its own `/amigos` and `/implement` runs continue to work
  under the refusal rather than around it.
- The new rule and the route through a legitimate contract change recorded in
  `docs/component-design/gate.md`.

## Out of Scope

- The contract change workflow — contract diffs and explicit reapproval — which
  README places in phase 8. This story refuses an edit and points at the existing
  declared state; it does not build the ceremony for making a change legitimate.
- Any configuration switch for the refusal. README section 31 forbids an escape
  hatch this project would not expect a downstream project to use, so an off
  switch this repository must never flip would be a strange thing to ship. Every
  adopting repository inherits the rule unconditionally.
- Governing `.amigos/config.json`, which carries `gate.exempt` and `stories_dir`
  and is itself exempt. It is an unguarded off switch for this very rule, and it
  is named by neither gap 5 nor this story. Recorded as a non-blocking question.
- The other v0.6 gaps, each separately sequenced: CI outside the session (3),
  `git commit --no-verify` (4), `.claude/settings.json` editable under a ready
  story (5), writes made through `Bash` (6), the dogfooding story-id allowlist
  (9), and `amigos check` rewriting `dor.json` on every run (10).
- Any change to `amigos verify`, whose baseline STORY-009 settled. Detection and
  refusal stay two mechanisms answering two questions.
- Any change to the seven Definition of Ready checks, the lint vocabulary, the
  declarable-state enum, or what readiness means.
- Removing `.amigos/**` from the exempt set, or beginning to govern `docs/**` or
  `.amigos/runs/**`.
- Refusing contract edits for stories that are not ready. A draft, blocked,
  `amigos_running` or `contract_change` story stays fully editable; that is
  contract authoring, and it is the work the exemption exists for.
- A test harness for the `PreToolUse` adapter. It is a thin adapter that imports
  `gate.decide()`, and `gate.md` already holds that adapters carry no rules, so
  the rule is judged through the command and the adapter inherits it.
- Retroactive judgement on contract edits already in this repository's history,
  including STORY-006's contract having been finalised in the commit that
  implemented it.
- Making bypass impossible. A maintainer with administrative rights can always
  merge anything. What this story removes is a route that exists for this project
  and not for the projects it asks to adopt it.

## Success

An agent that edits a ready story's `acceptance.feature` is stopped when it
tries, and stopped again if it stages the change, and in both cases is told which
story is ready and how to reopen it — rather than discovering the problem later
from a command nobody was obliged to run.

Nothing the protocol needs has become harder: `/amigos` still authors and revises
contracts in this repository, `/implement` still writes its run record and
commits its work while its story is ready, and a new story can still be
scaffolded, contracted, committed and closed out end to end.

Phase 6's first bullet has a mechanism behind it rather than a sentence, and no
exemption exists for Amigos Skills that a downstream project adopting the same
version would not also get.
