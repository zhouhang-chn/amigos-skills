# v0.2 Repository Gate — Implementation Notes

Story: **STORY-007**. Contract and plan were committed before any
implementation, in commit `a18c8f4`.

## The milestone's exit criterion, demonstrated

On a branch named `no-story-probe`, which names no story, with thirteen governed
files staged:

```text
gate: refused - 13 governed path(s) changed but no active story could be
resolved. Looked in: the AMIGOS_STORY environment variable; the
.amigos/ACTIVE pointer file; a story id in the branch name
```

The commit did not happen. On `story/STORY-007-repository-gate` the same staged
change is permitted, because the branch resolves STORY-007 and STORY-007 is
ready. The project is now subject to its own gate.

## Bugs found

### `lstrip("./")` strips characters, not a prefix

`is_exempt` normalised a path with `path.lstrip("./")`, intending to remove a
leading `./`. `str.lstrip` takes a *character set*, so `.amigos/stories/X` became
`amigos/stories/X` and stopped matching the `.amigos/**` exempt pattern — every
contract file was governed, which would have deadlocked the protocol exactly as
the design predicted.

Caught by the test derived from STORY-007's fifth scenario, which is the
argument for writing tests from the contract rather than from the code: the
scenario asserts that a change under `.amigos/` needs no story, and the
implementation quietly did the opposite.

### The shipped pre-commit hook only worked in this repository

The first version fell back to
`python3 "$(git rev-parse --show-toplevel)/scripts/gate.py"`, which assumes the
gated repository *is* the amigos-skills checkout — the one repository where a
gate matters least. Any other repository got a missing-file error from its own
commit hook.

Fixed by generating the hook at install time with the interpreter and the
package location resolved and baked in. The hand-written copy under
`integrations/git/` was deleted rather than kept in sync: two copies of one rule
drift, and this is the second time in two milestones that the fix has been to
delete the duplicate.

## Decisions taken during implementation

### The hook is generated, not shipped

`integrations/git/` now holds only a README showing what installation produces.
`amigos hooks install` is the single path, and it refuses to overwrite a
pre-commit hook amigos did not write, or to remove one.

### Ambiguity refuses rather than choosing

A branch name containing two story IDs could plausibly pick the longest match,
or the first. It refuses. A gate that guesses can be gamed by naming a branch
carefully, and the failure would be silent.

### `.amigos/ACTIVE` is gitignored

It is per-checkout state. Committing it would mean a branch carries someone
else's idea of what is being worked on.

## A test expectation that was wrong

`test_branch_matching_is_bounded_to_whole_story_ids` asserted that
`story/STORY-0071-other` resolves to nothing. It resolves to `STORY-0011`'s
longer sibling `STORY-0071`, correctly — the property under test is that
`STORY-007` must not match *inside* `STORY-0071`, and that holds. Expectation
corrected, code unchanged.

## Holes left open on purpose

Recorded in [gate.md](../../component-design/gate.md) rather than papered over:
an agent can disable the in-session hook by editing `.claude/settings.json`,
`git commit --no-verify` skips the pre-commit hook, and writes driven through
`Bash` are not gated. The first two are true of every in-session and pre-commit
hook ever written; CI in v0.6 is what closes them. The third is a non-blocking
open question on STORY-007, left until there is evidence the hole matters.

This milestone's target is README section 18's wording exactly — skipping the
contract should be *harder* than following it, not impossible.

## Verification results

```text
python -m pytest -q          187 passed
amigos check STORY-007       exit 0
amigos gate --staged         permitted on the story branch, refused off it
git commit                   refused by the installed hook on a branch naming no story
```

Every command in [action-plan.md](action-plan.md) was run and produced the
recorded result.

## Follow-ups

- v0.3 (`/amigos`) is now subject to the gate: its work needs a ready STORY-004
  on a branch that resolves it. That is the first real test of whether the gate
  is usable rather than merely correct.
- If the fail-closed exempt set causes repeated friction, README section 31 says
  to treat it as product feedback before adding an escape hatch.
