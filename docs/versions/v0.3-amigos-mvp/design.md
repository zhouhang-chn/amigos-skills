# v0.3 `/amigos` MVP — Design

Story: **STORY-004**.

## Shape

```text
/amigos STORY-123 "description"
        |
   [0] setup          amigos create | reopen; declare amigos_running
        |
   [1] Product        who, what problem, desired outcome, in/out of scope
   [2] Development    feasibility, dependencies, invariants, components
   [3] QA             primary path, counterexamples, judgeable assertions
        |
   [4] Challenge      Dev attacks scope, QA attacks ambiguity,
        |             Product attacks scope creep
        |
   [5] Interview      at most two rounds, only on what blocks the contract
        |
   [6] Synthesis      write the four input files
        |
   [7] Validate       amigos check  ->  repair  ->  re-check, up to 3 times
        |
   [8] Finish         declare draft; report ready or blocked
```

The skill drives; the deterministic tools judge. The model proposes a contract
and the validator decides whether it is one.

## The repair loop is the load-bearing part

A drafting agent that writes once and stops produces contracts that fail their
own validator, and the repair falls to a human — which is the work the project
exists to remove. So the skill runs `amigos check`, reads the named findings and
line numbers, fixes what it can, and re-checks.

Bounded at three attempts. An unbounded loop against a rule the model has not
understood is the failure mode worth avoiding first: it burns budget and ends in
the same place. On exhaustion the skill reports the remaining findings and
leaves the story in `draft`, rather than pretending either success or blockage.

## The interview is bounded, and blocking is the fallback

Two rounds of focused questions, asked only about things that would otherwise
become invented assumptions. Whatever remains goes to `open-questions.md` under
`## Blocking`, which withholds readiness through the ordinary check rather than
through anything special.

This is the middle of the two things README says. Section 24 prefers `blocked`
over invented certainty; section 23 says the system should surface uncertainty
rather than force humans to rewrite artifacts by hand. Asking first and blocking
second satisfies both, in that order.

## Three passes plus one challenge

README section 32 puts one orchestrating model here and splits the roles in
v0.4. The three passes are sequential and separately instructed. The challenge
pass exists so that v0.4 has something to beat: if independent subagents do not
find classes of problem the challenge pass misses, the multi-agent design does
not survive its own milestone.

Conflicts the challenge surfaces go into the contract — as a narrowed scope, an
added counterexample, or a blocking question — never into a commentary section.
The output is the contract, not the conversation.

## What the skill may not do

| Rule | Why |
|---|---|
| Never write `dor.json` | Readiness is derived. A skill that writes it is judging itself. |
| Never declare `ready` or `blocked` | Those are computed; the validator rejects them structurally anyway. |
| Never invent an assumption to clear a blocker | The blocker is the useful output. |
| Never record the discussion | Chat history is not authoritative; the contract is. |

The first two are enforced by code, not by the skill remembering them: `dor.json`
is validator-written, and `state.json` rejects both values. The skill's
instructions say so as well, so the rule is visible where it applies.

## New code

Only one thing is missing: nothing can record a lifecycle transition.
`amigos state <id> --set <state>` appends to `state.json`'s history and updates
`declared_state`, reusing the existing validation so `ready` and `blocked` are
refused there exactly as they are on read.

Everything else the skill needs already exists: `amigos create`, `amigos check`,
`amigos lint`.

## Placement

```text
skills/amigos/SKILL.md          the plugin's copy, declared in plugin.json
.claude/skills/amigos           a symlink, so this checkout dogfoods it
```

One file, two discovery paths, no second copy to drift.

## Alternatives rejected

- *Pure prompt with no repair loop.* Nothing new to maintain, but the skill
  would routinely hand back contracts that fail their own validator.
- *An `amigos draft` command emitting a worksheet.* More deterministic
  scaffolding, at the cost of inventing a second contract format beside the real
  one, which would drift from the templates.
- *Interviewing until no blocker remains.* An agent required to reach zero
  blockers has an incentive to accept a weak answer, which is how invented
  certainty gets in.
