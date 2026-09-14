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
        +--------------+----+-----------+---------------+
        |              |                |               |
  a ready story's  governed        active story?   dor.evaluate()
  contract file?   paths?          (env > file >   (recomputed,
  (fails OPEN)     (fail closed)    branch)         never read)
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

That exemption is also what left a *finished* contract unprotected, which is
what [the next section](#a-ready-storys-contract-is-frozen) closes.

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

## A ready story's contract is frozen

Closed in v0.6 by STORY-010. `.amigos/**` stays exempt — removing it deadlocks
the protocol — so this is a **second question asked alongside classification**,
not a change to what `governed` means. `classify()` keeps its path-only,
time-independent semantics because `verify` runs it over historical commits to
derive a baseline; a classification that consulted present-day readiness would
judge yesterday's commits by today's state.

```text
a changed path under stories_dir, named intent.md, constraints.md,
acceptance.feature or open-questions.md
        |
        +-- was the story ready BEFORE this change?  -- no --> permitted
                    |                                            (fails open)
                   yes
                    |
                 refused
```

**Before the change** is the whole of it. At edit time the working tree still
holds the pre-edit contract, so the tree answers. At commit time the tree already
holds the *edited* contract, so `HEAD` answers. Deriving it from the edited
content would permit the most damaging edits and refuse only the harmless ones:
deleting a counterexample is itself an edit that leaves a story unready.

This also settles the case that would otherwise deadlock the protocol a second
time. A contract absent from `HEAD` has never been committed, so there is nothing
to protect and the commit that first records a ready contract is permitted.

`state.json` is read live and is deliberately **not** a contract input file. It
is the control the protocol offers: declaring `contract_change` withholds
readiness and reopens the contract, without having to commit that declaration
first. `dor.json` stays writable for the same structural reason — the validator
is its only writer, and `amigos check` rewrites it on every run.

### It fails open, and that is deliberate

The gate's default is fail-closed. This one rule inverts it: a path is refused
only when the story that owns it **demonstrably** evaluates ready. A contract
with unparseable Gherkin, a missing file, or a story id with no directory is not
ready, and stays editable — otherwise a broken contract could never be repaired.

The cost is stated rather than hidden: corrupting `state.json` lifts the refusal.
So does writing `contract_change` into it by hand. Both are gap 8, and neither is
made worse by failing open, because the second is available anyway.

### What the refusal says

The existing refusal ends with `Make the story ready, then retry`. Under this
rule that guidance is backwards — the change is refused *because* the story is
ready — so a frozen-contract refusal names the story, the file, and
`amigos state <id> --set contract_change` instead.

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
| `.amigos/config.json` carries `gate.exempt` and is itself exempt, so a ready story permits switching this rule off | The same shape as the `.claude/settings.json` hole above, and no narrower | v0.6, with its sibling |
| `working_tree_paths()` still omits deletions, so `amigos gate` with no arguments misses a deleted contract file | `staged_paths()` is the collector every commit goes through, and it was fixed by STORY-010 | not yet scheduled |

The aim of this milestone is README section 18's wording exactly — that skipping
the contract is *harder* than following it. Impossibility is a later problem.
