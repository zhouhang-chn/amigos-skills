# Component Design: The Repository Gate

The gate is what turns the protocol from documentation into a constraint.
README section 18:

> The system must not depend on an agent voluntarily remembering the process.

## One decision, several adapters

```text
    Claude Code PreToolUse          git pre-commit
    (Edit, Write, NotebookEdit)     (every commit)
              |                            |
              +-------------+--------------+
                            |
                    gate.decide()
                            |
        +-------------------+-------------------+
        |                   |                   |
  governed paths?     active story?      dor.evaluate()
  (fail closed)       (env > file >      (recomputed,
                       branch)            never read)
```

Adapters collect changed paths, call the decision, and translate the exit code
into whatever their host expects. None holds a rule. Two implementations of one
rule drift, and the drift is invisible until the gate is wrong.

## Resolving the active story

First hit wins:

| Order | Source | Why |
|---|---|---|
| 1 | `AMIGOS_STORY` | explicit and per-command; scripts and CI use this |
| 2 | `.amigos/ACTIVE` | per-checkout; survives detached HEAD and worktrees |
| 3 | branch name | the default path; needs no extra state to go stale |

Branch parsing does not guess a pattern. It takes the story IDs that exist under
`stories_dir` and looks for each in the branch name, bounded so `STORY-001` does
not match inside `STORY-0011`. Zero matches is unresolved. Two or more refuses
rather than picking one — a gate that guesses is a gate that can be gamed by
naming a branch carefully.

`.amigos/ACTIVE` is gitignored. It is per-checkout state, not part of the
contract.

## Governed paths

Fail closed: a path is governed unless it matches an exempt pattern.

```json
"gate": { "exempt": [".amigos/**", "docs/**", "*.md", "LICENSE", ".gitignore"] }
```

The exempt set is exactly the work that makes a story ready. Gating the contract
files would deadlock the protocol: a story could never become ready, because
becoming ready requires editing a story.

Everything else is governed, including directories that do not exist yet. An
allowlist would leave every new directory unguarded until somebody remembered to
add it, so the gate would erode silently. Fail-closed is noisy exactly once, at
adoption.

`tests/` is governed deliberately. From v0.5 `/implement` writes tests from
`Then` clauses, so tests are implementation output; exempting them would put the
contract's own product outside the gate.

Glob matching is in-tree: `*` stops at a path separator, `**` crosses them, so
`*.md` means top-level Markdown rather than every Markdown file in the tree.

## Readiness is recomputed, never read

From v0.5 the gate is not the only component holding this rule: `amigos verify`
re-derives readiness the same way and reads `dor.json` for one thing only, the
recorded `contract_hash` baseline. README section 14 states the opposite and is
the text that needs correcting; see
[execution.md](execution.md).

The gate calls `dor.evaluate()` and ignores any committed `dor.json`. Two
reasons, and the second is the important one:

1. A record on disk describes the contract as it was when the record was
   written. The files may have changed since.
2. `dor.json` is writable by the very agent being gated. An agent that could
   grant itself passage by writing a file would not be gated at all.

## Exit codes

| Code | Meaning | Adapter behaviour |
|---|---|---|
| 0 | permitted | allow |
| 1 | refused | block and show the reason |
| 2 | the gate could not run | block and say so distinctly |

Code 2 covers a missing repository, unavailable git, or unreadable config. It is
separate from 1 because "you may not do this" and "I could not tell" need
different responses from a human.

## Known holes

Stated plainly, because a gate whose limits are undocumented invites false
confidence.

| Hole | Why it is tolerated here | Closed by |
|---|---|---|
| An agent can edit `.claude/settings.json` and disable the in-session hook | True of every in-session hook; the pre-commit hook is the backstop | v0.6, via CI that cannot be reached from the session |
| `git commit --no-verify` skips the pre-commit hook | True of every pre-commit hook | v0.6, via CI |
| Writes through `Bash` are not gated | Recorded as a non-blocking open question rather than fixed speculatively | to be decided on evidence |

The aim of this milestone is README section 18's wording exactly — that skipping
the contract is *harder* than following it. Impossibility is a later problem.
