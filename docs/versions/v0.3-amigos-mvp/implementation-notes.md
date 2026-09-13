# v0.3 `/amigos` MVP — Implementation Notes

Story: **STORY-004**, the last contract in this repository written by hand.
Committed before implementation in `3067aee`.

## The milestone's success criterion, met

README section 32:

> Amigos Skills can create usable contracts for its own development.

`.amigos/stories/STORY-005/` was produced by running the skill, not by hand, and
passes the same validator every hand-authored contract passes. All seven checks
passed on the **first** attempt; the repair loop was not needed.
`tests/test_dogfooding.py` keeps that as a regression rather than a claim.

## How the run actually went

Honest account, because the point of dogfooding is the evidence, not the
demonstration.

**The skill was not invoked as a registered skill.** It was created during this
session, so it was not in the session's skill list when the run started. The
phases were executed by following `SKILL.md` literally. That validates the
*instructions*, which is the substance, but it does not validate skill discovery
or invocation. Notably, the skill *did* become discoverable partway through the
run, which at least confirms the `.claude/skills/amigos` symlink is found. The
first genuine end-to-end invocation will be v0.4's.

**The challenge phase earned its place.** Phase 4 surfaced two things the three
drafting passes had not:

1. STORY-005's exit criterion — "the three agents discover different classes of
   ambiguity" — had no definition of *different*, so QA could not write a
   judgeable `Then` for it. The milestone's own kill criterion was unfalsifiable.
2. Building a comparison method looked like scope creep against "split the roles
   into three subagents", and might belong to a separate story.

Both were escalated to Phase 5 and asked. That is the intended path working:
the challenge found what the drafting passes missed, and the interview resolved
what the challenge could not.

**The interview used one round of two, and blocked on nothing.** Both questions
were answered, so `open-questions.md` carries no blocking entry. The resolutions
are visible in the contract: findings are structured records so overlap is
counted, and the three roles draft blind before a reconciliation pass.

**One deferral was recorded rather than silently dropped.** A bounded challenge
round between drafting and reconciliation was considered and put under
`## Out of Scope` with its reason, plus a non-blocking open question about when
to revisit. That is the behaviour the contract asks for — a decision not taken is
still a decision recorded.

## What this run does not prove

- The repair loop was never exercised, because nothing failed. Its behaviour
  under a validator rejection remains untested against a real run.
- One contract is one data point, and the same session wrote the skill and ran
  it. The stronger evidence is v0.4, where the skill runs with agents whose
  prompts this session did not write.

## Decisions taken during implementation

### `amigos state` was the only code the skill needed

Everything else already existed. `state.json` was written once by scaffolding and
never again, which made `amigos_running` and `contract_change` unreachable in
practice. The command appends to history rather than replacing it — a contract's
lifecycle is evidence — and refuses `ready` and `blocked` at the write end
exactly as `read_state` refuses them at the read end, so the rule holds from
whichever side something approaches the file.

### The skill is tested against the code, not for behaviour

A prompt cannot be unit tested for what a model will do with it. It can be held
to the rules the code enforces, which is what `tests/test_skill.py` does: it
fails if the skill names a command that does not exist, a lifecycle state that is
not declarable, or a Definition of Ready check the validator does not compute.

The most valuable of these asserts that the vague-word list in the skill still
matches the linter's. A skill teaching an agent to write clauses the linter
rejects would make the repair loop do work that never needed doing, and nothing
else in the system would notice.

### One file, two discovery paths

`skills/amigos/SKILL.md` is the plugin's copy; `.claude/skills/amigos` is a
symlink to it. A test asserts the link resolves to the shipped file rather than a
duplicate. This is the third time in three milestones that the right answer was
to delete the second copy instead of keeping two in sync.

## Verification results

```text
python -m pytest -q                    219 passed
amigos check STORY-004                 exit 0
amigos state STORY-004 --set ready     exit 2, state unchanged
amigos check STORY-005                 exit 0   (generated, not hand-authored)
amigos status                          six stories, all ready, exit 0
```

## Follow-ups

- v0.4 runs the skill as a registered skill for the first time, which is the
  test this milestone could not perform on itself.
- The repair loop needs a run where the validator actually rejects something.
  v0.4's first attempt is the natural place to watch for it.
