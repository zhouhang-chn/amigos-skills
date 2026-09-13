# Constraints

## Technical Constraints
- The baseline must name a revision the judged agent cannot move by an ordinary
  action. The chosen revision is the parent of the earliest commit changing a
  governed path for this story; a later contract commit is newer than it and so
  cannot become it.
- Readiness stays recomputed from the contract files and is never read from a
  committed `dor.json`. This story changes what the contract is compared
  against, not where readiness comes from.
- `amigos verify` writes nothing into the story directory. Every git invocation
  it makes is read-only with respect to the contract files.
- Difference is computed the way git computes it. Comparing working-tree bytes
  against blob bytes is not equality-safe under `core.autocrlf`, `text=auto` or
  any clean/smudge filter. This checkout has no `.gitattributes`, so a defect
  here would not show up in this repository.
- Paths handed to git are relative to the git work-tree root. `Config.root` is
  the nearest ancestor containing `.amigos/` and need not be that root, and
  `--stories-dir` can point at a corpus outside the work tree entirely.
- The exit-code vocabulary is fixed: 0 verified, 1 evaluated and not verified,
  2 unanswerable. Every new git-side failure lands on one of these by decision.
- Which paths count as governed is the gate's existing classification. A second
  definition of governed would drift from the first.
- The runtime stays stdlib-only on Python 3.11+. git is invoked as a subprocess,
  as `src/amigos/gate.py` already does; no packaged dependency is added.
- `.amigos/` stays platform-independent. No git revision or branch name is added
  to `.amigos/config.json`.

## Dependencies
- git as an executable and as repository state: a work tree, at least one
  commit, and the four contract files tracked.
- `dor.evaluate()` for readiness; `story.HASHED_FILES` for which four files
  constitute the contract; `gate.classify()` for which paths are governed.
- `tests/conftest.py::git_repo` is the only git-backed fixture. Every current
  `verify` test uses `scratch_repo`, which is not a git repository, so fixture
  work is part of this story rather than incidental to it.
- The story's own contract must be committed before an implementation run can be
  verified against history.

## Invariants
- The protocol must not deadlock. A contract produced by the amigos skill stays
  committable after the story computes ready, and a story stays re-contractable
  after `contract_change`.
- `state.json` and `dor.json` stay writable while a story is ready. Neither is
  in `HASHED_FILES`, and that exclusion is load-bearing.
- Readiness stays derived, never declared. The validator remains `dor.json`'s
  only writer.
- A question that cannot be answered never reads as verified.
- This repository stays held to whatever it ships: `tests/test_dogfooding.py`
  keeps passing, and no exemption is added for amigos-skills that a downstream
  project would not get.
- Closeout still passes: the test suite, `amigos status` exit 0, and
  `amigos gate --staged` permitted.

## Relevant Components
- src/amigos/verify.py
- src/amigos/cli.py
- src/amigos/gate.py
- src/amigos/story.py
- tests/test_verify.py
- tests/test_cli.py
- tests/conftest.py
- docs/component-design/execution.md
