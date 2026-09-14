# v0.6 Strong Self-Hosting Enforcement — Design

The milestone's stories, in order, with the first one designed in full.

| Story | Scope | Status |
|---|---|---|
| STORY-009 | Contract immutability: the baseline moves to git history | contracted |
| STORY-010 | The gate refuses a contract edit while a story is ready | contracted |
| — | Enforcement outside the session: CI over a push range | not contracted |
| — | Governed writes made through `Bash` | not contracted |
| — | Blocked stories and a hand-edited `state.json` | not contracted |

STORY-008 is not in this list. README section 26 reserves it for eval export in
phase 7, and STORY-006's ready contract references that allocation, so freeing
the id would mean editing a ready contract — the act this milestone exists to
prevent. Ids here follow section 26's allocation rather than creation order,
which is already true of STORY-007.

---

## STORY-009 — contract immutability

### The question and the wrong answer

`amigos verify` asks whether the requirement was redefined during
implementation. It answers by hashing the four contract files in the working
tree against `dor.json.contract_hash`.

```text
  working tree  ──hash──┐
                        ├── equal?  ──> verified
  dor.json ─────────────┘
       ^
       └── rewritten by `amigos check`, which /implement's Phase 0 runs
```

Both sides of the comparison are writable by the agent being judged, and the
command that rewrites one of them is a command the skill instructs the agent to
run. The check does not fail; it is answered by erasing the question.

### The baseline

The baseline is **the parent of the earliest commit, reachable from the current
commit, that changes a governed path for this story**.

```text
  newer
    │   e4f1a2   tests/, src/           implementation continues
    │   b9c7d3   acceptance.feature     a contract edit, committed
    │   a2d5e8   src/verify.py          FIRST governed change  ── I0
    │   7c1b04   .amigos/, docs/        the contract commit     ── I0^  BASELINE
  older
```

`b9c7d3` is newer than `I0`, so it cannot become the baseline. That is the whole
point of the choice, and it is what separates this from the two alternatives.

**Derivation.** Two git queries and a classification that already exists:

1. `C0` — the oldest commit reachable from HEAD that touches any of this story's
   four contract files. No `C0` means the contract was never committed.
2. `I0` — the oldest commit in `C0..HEAD` that touches a governed path, where
   governed is `gate.classify()` and not a second definition.
3. The baseline is `I0^`. With no `I0`, implementation has not been committed
   yet and the baseline is HEAD.

**Why not HEAD.** `git commit` moves it, which re-opens the hole one level up.
Development stated the property as a constraint — *the baseline must name a
revision the judged agent cannot move by an ordinary action* — and HEAD fails it.

**Why not merge-base with an integration branch.** Semantically the cleanest
reading of "during implementation", and wrong in this repository as it actually
is: `merge-base(HEAD, main)` is `ac5f549` (v0.3), long before STORY-006's
contract existed, so the whole contract would report as changed. It also needs a
git ref in `.amigos/config.json`, and `.amigos/` is deliberately
platform-independent.

### Comparison is git's, not ours

`story.hash_inputs()` reads bytes. Comparing those bytes against a blob is not
equality-safe under `core.autocrlf`, `text=auto`, or any clean/smudge filter: a
file git considers unchanged would report as differing. This checkout has no
`.gitattributes`, so the defect would not appear here and would appear
downstream.

The comparison therefore asks git, which applies the repository's own filters,
rather than comparing hashes computed two different ways.

### Paths

Paths handed to git are relative to the **work-tree root**, which is not
necessarily `Config.root` — that is the nearest ancestor holding `.amigos/`, and
`--stories-dir` can point at a corpus outside the work tree entirely. Resolving
one to the other is part of the work, not an assumption.

### Exit codes

The existing vocabulary is fixed and every new git-side failure lands on one of
the three by decision rather than by falling through:

| Code | Meaning | New cases |
|---|---|---|
| 0 | verified | — |
| 1 | evaluated, not verified | the contract differs from the baseline |
| 2 | unanswerable | no git, no work tree, no commits, contract never committed |

The invariant behind the split: *a question that could not be answered never
reads as verified*.

### `dor.json.contract_hash` stays

It is `required` in `schemas/dor.schema.json` under `additionalProperties:
false`, present in every committed `dor.json`, and asserted by two tests in
`tests/test_dogfooding.py`. Retiring it is a schema-and-corpus change that buys
little while it still answers the question in a checkout without git. The git
baseline becomes the authority; the recorded hash stays as a record.

### Tests

Every current `verify` test runs on `scratch_repo`, which has no `.git`. The
`git_repo` fixture exists but nothing in `test_verify.py` uses it. Building a
git-backed fixture that can commit a contract, then commit a governed change,
then commit a contract edit — the three-commit shape the baseline derivation
turns on — is part of this story rather than incidental to it.

### What this still does not catch

Stated here because v0.5 stated its own limit here, and because a mechanism
whose edges are undocumented invites false confidence.

- **A rebase.** History reachable from HEAD is what the baseline is derived
  from, so rewriting that history moves it. Deliberate history rewriting is a
  louder act than re-running a command, and it is not treated as the same class
  of problem.
- **A contract edited before any governed change.** That is contract authoring,
  and it is legitimate.
- **The write itself.** Nothing refuses the edit; this story detects it. Refusal
  is the next story, and Development's drafting showed why it is not a one-line
  addition: edit-time and commit-time refusal are different rules, and a
  commit-time refusal scoped to the story directory would refuse this project's
  own closeout commits.


---

## STORY-010 — the gate refuses a contract edit while a story is ready

### A second question, not a wider exempt set

`.amigos/**` must stay exempt. Removing it gates the work that makes a story
ready, and a story could then never become ready at all. So the refusal is asked
**alongside** classification rather than expressed through it:

```text
  decide(paths, staged)
        |
        +-- frozen_contracts()  a contract file whose story was ready
        |         |             BEFORE this change            -> refused
        |
        +-- classify()          governed unless exempt
        +-- resolve_story()     env > pointer > branch
        +-- dor.evaluate()      recomputed, never read
```

`classify()` could not carry it. `verify._governed_in()` calls that function over
**historical** commits to derive STORY-009's baseline, so a classification that
consulted present-day readiness would judge yesterday's commits by today's state
and move the baseline STORY-009 was built to fix.

### Before the change

```text
  edit time    working tree      still holds the pre-edit contract
  commit time  HEAD              the tree already holds the edited one
```

This is the decision the three roles converged on independently and none could
resolve. An edit that deletes a counterexample leaves the story unready, so a
rule that derives readiness from the edited content permits exactly the edit it
exists to refuse, and refuses only the harmless ones.

Reading `HEAD` at commit time also disposes of the deadlock the milestone's own
design predicted. A contract absent from `HEAD` was never committed, so there is
nothing to protect and the commit that first records a ready contract is
permitted — without a special case for it.

`state.json` is read live, not from `HEAD`. It is not a contract input file, and
it is the control the protocol already offers: declaring `contract_change`
reopens the contract without having to commit that declaration first.

### Failing open, on purpose

The gate's default is fail-closed. This rule inverts it: only a story that
**demonstrably** evaluates ready freezes its contract. Unparseable Gherkin, a
missing file, or a story id with no directory all leave the contract editable,
because a broken contract that cannot be repaired is worse than one that can be
edited.

The cost is real and is written down rather than discovered: corrupting
`state.json` lifts the refusal. So does writing `contract_change` into it by
hand, which is available anyway — both are gap 8, task 5 of this milestone.

### What this still does not catch

- **`.amigos/config.json`.** It carries `gate.exempt` and `stories_dir`, it is
  itself exempt, and a ready story permits editing it. It is the same shape as
  the `.claude/settings.json` hole, which gap 5 owns, and it is named by neither.
- **A deletion in the working tree.** `staged_paths()` now collects `D`;
  `working_tree_paths()` does not, so `amigos gate` with no arguments still
  misses one.
- **Writes through `Bash`, and `--no-verify`.** Gaps 6 and 4. An edit-time rule
  that the tool never reaches is not an edit-time rule, which is why the refusal
  holds at commit time too.
