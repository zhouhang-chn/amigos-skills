# Component Design: Execution

The `/implement` skill turns a ready contract into code, tests and a report, or
stops and says why. It is the consumer on the other side of every artifact the
rest of the system produces.

## The division of labour

```text
skill (a model)                   deterministic tools
  writes tests from Then clauses    decide whether the story may be worked on
  writes the minimum code           decide whether the contract still matches
  judges what a test cannot         refuse a write to a governed path
  reports coverage and scope        name the file that moved
```

The model never judges whether it honoured the contract. `amigos verify` answers
that, and the skill does not get to summarise it in its own favour — the same
division `/amigos` uses, applied to the other half of the loop.

## Phases

| Phase | Does |
|---|---|
| 0 Resolve | re-derive readiness; refuse unless ready; make the story resolvable |
| 1 Load | the four contract files are the specification |
| 2 Cover | map every scenario to the test or judgement that decides it |
| 3 Red | a test for absent behaviour fails before the source changes |
| 4 Implement | the minimum those tests require; run the suite |
| 5 Report | coverage, changed files against scope, unsatisfied scenarios |

## What a skill may never do

| Never | Why |
|---|---|
| Edit a contract input file | The contract is what the work is judged against. Editing it is marking your own exam. `.amigos/**` is exempt from the gate, so this rule has to hold without enforcement — which is why `amigos verify` makes its violation visible. |
| Write `dor.json`, or declare `ready` / `blocked` | Readiness is derived. The validator is its only writer. |
| Treat a recorded `ready: true` as authority | That file is writable by the agent being gated. |
| Skip or delete a test derived from a `Then` | An unsatisfied scenario is a result; hiding it turns a known gap into an unknown one. |
| Route around a gate refusal | No change to this project may bypass a rule the same version would impose on another project. |
| Invoke `/amigos` on a contract conflict | One session must not both discover a conflict and author the criterion that replaces it. |

## Verification: `amigos verify`

```text
readiness   re-derived from the contract files      (never read from dor.json)
baseline    the parent of the earliest commit changing a governed path
contract    each input file in the tree  vs  that revision, compared by git
verified    ready and nothing changed
exit        0 verified | 1 not verified | 2 no committed contract, or unusable
```

`verified` is computed and never stored. Adding a second persisted verdict
would recreate the problem `dor.json` already has: a file that says a thing is
true, writable by the agent it constrains.

### The baseline, and why it is not HEAD

Closed in v0.6 by STORY-009. The baseline is **the parent of the earliest commit
that changes a governed path for the story**, so a contract edit committed during
implementation is newer than the baseline and cannot become it.

HEAD was rejected for the reason the roles drafting STORY-009 all reached
independently: `git commit` would move it, re-opening the hole one level up.
Merge-base with an integration branch was rejected because it requires that
branch to be current, and in this repository it is not.

`dor.json.contract_hash` stays. It is required by the schema, present in every
committed `dor.json`, and still the only answer available in a checkout without
git. It is a record; history is the authority.

What this still does not catch is a rebase, which rewrites the history the
baseline is derived from. That is a louder act than re-running a command, and is
not treated as the same class of problem.

## Coverage is stated, never rounded up

Some `Then` clauses describe behaviour no test in a repository can observe —
assertions about how an agent behaves, about what a prompt contains. The skill
names them with the judgement method used instead and **excludes them from the
count of scenarios decided by tests**.

Silently skipping the clauses that are hard to test, and reporting the contract
as verified, is the failure this rule exists to prevent. A run that reports
"8 of 10 decided by tests" is more useful than one reporting ten.

## Where a run's evidence lives

```text
.amigos/stories/<id>/     the specification
.amigos/runs/<id>/        evidence about runs, drafting and implementation alike
```

The story directory holds the contract and nothing else, settled by STORY-005.
An implementation run writes its report beside the drafting evidence for the same
story, never inside it.

## The conflict path

```text
/implement  ->  conflict found  ->  report  ->  contract_change  ->  stop
                                                                     |
                                                          a human runs /amigos
```

Declaring `contract_change` withholds readiness the moment it happens, and the
gate then refuses every governed write — including committing the work already in
the tree. So it is declared **last**, after the report exists. Whether partial
work should be saveable across a conflict at all is an open question for v0.6.
