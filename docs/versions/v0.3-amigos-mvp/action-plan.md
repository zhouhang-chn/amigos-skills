# v0.3 `/amigos` MVP — Action Plan

Story covered: **STORY-004**.

## Tasks

| Status | Task | Acceptance |
|---|---|---|
| [ ] | `amigos state` subcommand | Records a transition; refuses `ready` and `blocked` |
| [ ] | `skills/amigos/SKILL.md` | Eight phases, the four prohibitions, bounded interview and repair |
| [ ] | Plugin manifest declares `skills/` | `plugin.json` points at the directory that now exists |
| [ ] | `.claude/skills/amigos` symlink | This checkout discovers the same file the plugin ships |
| [ ] | Tests for `amigos state` and the skill's stated discipline | One test per STORY-004 scenario that code can reach |
| [ ] | Use the skill to author the next story's contract | A generated contract passes the validator |
| [ ] | Docs: component design, roadmap, README sections 8, 9, 19 | Match the implementation |

## Verification

```bash
python -m pytest -q
amigos check STORY-004                                  # exit 0

amigos state STORY-004 --set amigos_running             # exit 0
amigos state STORY-004 --set ready                      # exit 2, unchanged
amigos state STORY-004 --set draft                      # exit 0, history preserved

amigos check STORY-005                                  # the generated contract, exit 0
amigos status                                           # every story ready
```

The milestone's own success criterion, from README section 32:

> Amigos Skills can create usable contracts for its own development.

It is met when a contract this repository did not hand-author passes the same
validator every hand-authored contract passes.

## Risks

| Risk | Mitigation |
|---|---|
| The skill produces contracts that satisfy the checks while saying nothing | The checks are a floor, not a definition of quality; the generated contract is reviewed by a human before the milestone closes, and weak output is product feedback. |
| The repair loop edits `acceptance.feature` toward whatever passes the lint | The lint rejects unjudgeable wording, not content, so passing it requires stating an observable outcome rather than removing the assertion. Reviewed in the generated contract. |
| One model produces three paraphrases rather than three perspectives | The exact risk section 32 names. The challenge pass is the mitigation, and v0.4 is the test of whether it worked. |
