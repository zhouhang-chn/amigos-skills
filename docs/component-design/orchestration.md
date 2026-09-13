# Component Design: Contract Orchestration

The `/amigos` skill turns a story id and a description into a contract that
passes the Definition of Ready, or into a story that is explicitly blocked with
the questions that stopped it.

## The division of labour

```text
skill (a model)                 deterministic tools
  proposes a contract             decide whether it is one
  asks what it cannot determine   refuse what an agent may not declare
  repairs what was rejected       name the file, line and rule
```

The model never judges its own output. `amigos check` does, and `dor.json` has
one writer that is not the skill.

## Phases

| Phase | Does |
|---|---|
| 0 Set up | create or reopen; declare `amigos_running`; read the repository |
| 1 Product | user, problem, outcome, why now, in and out of scope |
| 2 Development | feasibility, dependencies, invariants, components |
| 3 QA | primary path, counterexamples, judgeable assertions |
| 4 Challenge | each perspective attacks the others' output |
| 5 Interview | at most two rounds, only on what would become an assumption |
| 6 Synthesise | write the four input files |
| 7 Validate | `amigos check`, repair, re-check, at most three attempts |
| 8 Finish | return to `draft`; report ready or blocked |

`amigos_running` withholds readiness for the whole run, so a half-written
contract can never read as ready to anything downstream — including the gate.

## The two bounds

**The interview is bounded at two rounds.** README section 24 prefers `blocked`
over invented certainty; section 23 says the system should surface uncertainty
rather than make humans rewrite artifacts by hand. Asking first and blocking
second satisfies both, in that order. An agent required to reach zero blockers
has an incentive to accept a weak answer, which is how invented certainty gets
in.

**The repair loop is bounded at three attempts.** A drafting agent that writes
once and stops hands back contracts that fail their own validator, leaving the
repair to a human — the work this project exists to remove. An unbounded loop
against a rule the model has not understood is the opposite failure: it burns
budget and ends in the same place. On exhaustion the skill reports the remaining
findings and leaves the story in `draft`, claiming neither success nor blockage.

## What the skill may not do

| Never | Enforced by |
|---|---|
| Write or edit `dor.json` | code — the validator is its only writer |
| Declare `ready` or `blocked` | code — `amigos state` and `read_state` both refuse |
| Invent an assumption to clear a blocker | the instructions, and review |
| Write a commentary or transcript file into the story | the instructions, and review |

The first two are refused by code rather than by the skill remembering them. The
second two are only as strong as the instructions and the reviewer, which is
stated plainly rather than implied.

## Repairing without hollowing out

The failure mode worth naming: a repair loop pointed at a validator will find
the cheapest way to satisfy it. Deleting a counterexample satisfies a count.
Removing an assertion satisfies the lint.

The lint is built so this does not pay — it rejects unjudgeable *wording*, not
content, so the cheapest way to pass is to state the observable outcome. The
skill says so explicitly. It remains something a reviewer should look for.

## Placement

```text
skills/amigos/SKILL.md      the plugin's copy, declared in plugin.json
.claude/skills/amigos       a symlink, so this checkout dogfoods the same file
```

One file, two discovery paths, no second copy to drift. `tests/test_skill.py`
asserts the symlink resolves to the shipped file rather than a duplicate.

## Held to the code

A prompt cannot be unit tested for behaviour, but it can be held to the rules the
code enforces. `tests/test_skill.py` fails when the instructions drift: if the
skill names a command that does not exist, a lifecycle state that is not
declarable, a Definition of Ready check the validator does not compute, or if
the vague-word list in the skill stops matching the one the linter uses. That
last one matters most — a skill teaching an agent to write clauses the linter
rejects would make the repair loop do work that never needed doing.
