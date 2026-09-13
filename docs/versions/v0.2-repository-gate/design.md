# v0.2 Repository Gate — Design

Story: **STORY-007**.

## One decision, two adapters

```text
            .claude/settings.json          .git/hooks/pre-commit
            PreToolUse on Edit/Write       every commit
                     |                              |
                     +--------------+---------------+
                                    |
                              amigos gate
                                    |
              +---------------------+---------------------+
              |                     |                     |
      governed paths?        active story?           dor.evaluate()
      (fail closed)          (env > file > branch)   (recomputed, not read)
```

The adapters hold no rules. They collect changed paths, call the command, and
translate its exit code into the form their host expects. Anything else would
put two implementations of the rule in the repository, and they would drift.

## Resolving the active story

In order, first hit wins:

| Source | Shape | Why it exists |
|---|---|---|
| `AMIGOS_STORY` | environment variable | explicit, per-command, scriptable |
| `.amigos/ACTIVE` | first non-blank line | per-checkout, survives detached HEAD |
| branch name | any existing story id appearing in it | the default path, needs no extra state |

Branch parsing does not guess at a pattern. It takes the story IDs that actually
exist under `stories_dir` and looks for each in the branch name, bounded so that
`STORY-001` does not match inside `STORY-0011`. Zero matches is unresolved; two
or more is ambiguous and refuses rather than picking one.

This is why the branch for this milestone is `story/STORY-007-repository-gate`:
the convention is the mechanism.

## Governed paths

Fail closed. A path is governed unless it matches an exempt pattern.

```json
"gate": {
  "exempt": [".amigos/**", "docs/**", "*.md", "LICENSE", ".gitignore"]
}
```

The exempt set is exactly the work that makes a story ready. Gating the contract
files would deadlock the protocol: a story could never become ready, because
becoming ready requires editing a story. Docs are exempt for the same reason
that gap analysis precedes implementation.

Everything else — `src/`, `scripts/`, `schemas/`, `templates/`, `tests/`,
`pyproject.toml`, `integrations/`, and any directory added later — is governed
the day it appears. `tests/` is deliberately governed: from v0.5 `/implement`
writes tests from `Then` clauses, so tests are implementation output, and
exempting them would place the contract's own product outside the gate.

Glob matching is implemented in-tree: `*` does not cross a path separator, `**`
does. That keeps `*.md` meaning top-level Markdown rather than every Markdown
file in the tree.

## Readiness is recomputed, never read

The gate calls `dor.evaluate()` and ignores any committed `dor.json`. A record
on disk describes the contract as it was when the record was written; the files
may have changed since. The ninth scenario of STORY-007 fixes this: a story
whose `dor.json` says ready, but whose `acceptance.feature` has since lost its
counterexamples, is refused.

This also closes the obvious bypass. An agent that can write files could write a
`dor.json` saying `ready: true`; since nothing reads it, nothing happens.

## Exit codes

| Code | Meaning | Adapter behaviour |
|---|---|---|
| 0 | permitted | allow |
| 1 | refused | block, and show the reason |
| 2 | the gate could not run | block, and say so distinctly |

Code 2 covers a missing repository, unavailable git, or unreadable config. It is
separate from 1 because "you may not do this" and "I could not tell" need
different responses from a human.

## Known limits, and why they are acceptable here

- **The Claude Code hook is bypassable by editing `.claude/settings.json`.**
  Any in-session hook is. The pre-commit hook is the backstop, and CI in v0.6 is
  the one that cannot be reached from inside the session at all.
- **`git commit --no-verify` skips the pre-commit hook.** Also true of every
  pre-commit hook ever written. The aim of this milestone is README section 18's
  wording — that skipping the contract is *harder* than following it — not that
  it is impossible. Impossibility is v0.6's problem.
- **Bash-driven writes are not gated.** Recorded as a non-blocking open question
  rather than fixed speculatively.

## Alternatives rejected

- *Allowlist of governed globs.* Quieter to adopt, but every new directory is
  unguarded until somebody remembers to add it, so the gate erodes silently and
  invisibly. Fail-closed is noisy exactly once, at adoption.
- *Inferring the story from `Relevant Components`.* No extra state, but it makes
  enforcement depend on the accuracy of prose and breaks the moment two stories
  touch the same directory.
- *Trusting the committed `dor.json`.* One fewer evaluation per call, at the
  cost of making the gate's authority a file the gated agent can write.
