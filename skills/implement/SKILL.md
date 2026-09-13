---
name: implement
description: Build a ready story from its acceptance contract. Turns Then clauses into tests, implements the minimum those tests require, runs the suite, and reports coverage, scope and unsatisfied scenarios. Refuses to start on a story that is not ready, and never edits acceptance criteria. Use when implementing a story that already has a contract, or when asked to run /implement.
---

# Implement: build what the contract says

The contract is the specification. Your memory of the conversation is not.

**The output is working code plus an honest report.** A green suite that was
reached by changing what the contract asked for is the single failure this skill
exists to prevent.

## What you may never do

These six hold for the whole run.

| Never | Why | Held by |
|---|---|---|
| Edit `intent.md`, `constraints.md`, `acceptance.feature` or `open-questions.md` | The contract is what you are judged against. Editing it is marking your own exam. `.amigos/**` is exempt from the gate, so nothing stops you — this is the rule that has to hold without enforcement. | you, visible via `amigos verify` |
| Write or edit `dor.json` | Readiness is derived. The validator is its only writer. | you |
| Declare `ready` or `blocked` in `state.json` | Those are computed. `amigos state` refuses both. | code |
| Take a `ready: true` out of `dor.json` as authority | That file is writable by the agent being gated and may be stale. Re-derive it. | you, and by `amigos verify` |
| Delete, skip or `xfail` a test derived from a `Then` clause to finish | An unsatisfied scenario is a result. Hiding it converts a known gap into an unknown one. | you |
| Edit the gate's settings, uninstall the pre-commit hook, or commit with it skipped | No change to this project may bypass a rule the same version would impose on another project. | you |

## Phase 0 — Resolve

```bash
amigos check <STORY-ID>          # exit 0 and 'ready: true', or you stop here
```

Recompute readiness; never read the verdict out of `dor.json`. If the story is
not ready, **stop before touching any governed file**. Report the story and the
check that failed, and add no test file for it. A story that is not ready is not
a smaller job — it is a different job, and it belongs to `/amigos`.

Then make the story resolvable to the gate, so governed writes are permitted:

```bash
git switch -c story/<STORY-ID>-<short-description>
```

If the gate refuses anyway, report its message and the story id it could not
resolve. Do not route around it.

## Phase 1 — Load

Read all four contract files. `acceptance.feature` says what must be true;
`constraints.md` says what must survive; `intent.md` draws the scope;
`open-questions.md` names what was left undecided.

A non-blocking open question is not permission to decide it silently. If the work
forces one, that is a discrepancy for the report.

## Phase 2 — Cover

Map **every** scenario to the thing that decides it, before writing code:

```text
scenario  ->  the test that judges it
scenario  ->  the judgement method, when no test in this repository can observe it
```

Some `Then` clauses cannot be expressed as automated tests — assertions about how
an agent behaves, about what a prompt contains, about a human's reading. Name
them and say what judges them instead. Then **exclude them from the count of
scenarios decided by tests**, so the coverage number stays honest.

Silently skipping the clauses that are hard to test, and reporting the contract
as verified, is the failure mode this phase exists to prevent.

## Phase 3 — Red

For behaviour the repository does not have yet, write the test and **run it
against the unchanged source before writing any implementation**. Record that it
failed.

A test written after the code passes on its first run and proves nothing about
intent. This is the step that makes the test a judgement of the contract rather
than a description of whatever was built.

Where behaviour already exists, say so rather than manufacturing a baseline.

## Phase 4 — Implement

Write the minimum those tests require. Then:

```bash
<the repository's test command>      # here: python -m pytest -q
```

Honour `constraints.md`. An invariant it names is not advisory: if the minimum
implementation would break one, you have found a contract problem, not a reason
to break the invariant.

**If implementation proves the contract wrong** — a `Then` that contradicts a
constraint, a scenario that cannot be satisfied as written, a requirement the
system cannot carry — then, in this order:

1. Report the conflict: name the scenario and the clause it conflicts with.
2. Leave `acceptance.feature` byte-identical. Verify that it is.
3. `amigos state <STORY-ID> --set contract_change --note "<the conflict>"`
4. **Stop.** Do not invoke the amigos skill yourself.

Declare `contract_change` **last**, after the report exists. It withholds
readiness the moment it is declared, and the gate then refuses every governed
write — including committing the work already in the tree.

You do not run `/amigos` because one session must not both discover a conflict
and author the criterion that replaces it. A human decides.

## Phase 5 — Report

```bash
amigos verify <STORY-ID>         # re-derives readiness, diffs the contract
```

`verified: true` is the claim that the requirement was not redefined. If any
contract file differs, say so plainly — do not re-run `amigos check` to make the
hash match, which rewrites the baseline and answers the question by erasing it.

Report, in the run record and to the user:

- **Coverage.** Every scenario, with the test or judgement method that decides
  it, and the count decided by tests stated separately.
- **Test results.** The command and its outcome, verbatim.
- **Changed files.** Every changed governed file with the scenario or constraint
  it serves. Anything serving neither goes under **scope expansion** — report it
  and keep going; do not stop the run, and do not quietly keep it unreported.
- **Unsatisfied scenarios.** Any test still failing stays in the suite, unskipped,
  and the story is not reported as implemented.
- **Discrepancies.** Anything the contract assumed that turned out not to hold.

Write the run record beside the drafting evidence, never inside the story
directory:

```text
.amigos/runs/<STORY-ID>/<run-id>/implementation.md
```

The story directory holds the specification. Evidence about a run lives outside
it.

## What finishing looks like

```bash
python -m pytest -q              # the suite, including the new tests
amigos verify <STORY-ID>         # verified: true
amigos status                    # every story ready, exit 0
amigos gate --staged             # this slice's own changes permitted
```

A run that ends with an unsatisfied scenario and an accurate report has
succeeded at its job. A run that ends green because the contract moved has not.
