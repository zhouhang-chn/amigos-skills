# v0.4 Independent Subagents — Implementation Notes

Story: **STORY-005**. Implementation committed in `e0f2c56`.

## Status: complete, measured on the re-run

The milestone's exit criterion was evaluated on 2026-09-13 and passed. The run
that evaluated it is `.amigos/runs/STORY-006/2026-09-13T14-42-45Z`.

```text
50 findings, 30 distinct
product   20 findings,   4 named by no other role
dev       16 findings,   8 named by no other role
qa        14 findings,   8 named by no other role
shared 10   unique 20        split_added_nothing: false
```

Twenty findings were named by exactly one role. The criterion asked for a number
greater than zero, so the multi-agent design earns its cost and survives. The
section below records the first attempt, which produced no count.

The two things the milestone could not test on itself were both tested on this
run, and both held:

- **Agent registration works.** `subagent_type: product`, `dev` and `qa` all
  resolved. The three roles ran as registered agent types, so the
  `tools: Read, Grep, Glob, Write` restriction in their frontmatter was
  structural rather than an instruction a general-purpose agent could ignore.
- **The shared-vocabulary guard did its job.** Ten findings collided across
  roles on `(target_section, risk_dimension)` — including all three roles
  landing on the missing eval harness — which is the count behaving as a
  measurement rather than as a reward for coining new words.

What the split actually bought, on this run: Development alone found that
declaring `contract_change` withholds readiness and therefore blocks committing
the partial work already in the tree. QA alone found that the ticket named no
prohibition on the obvious escapes from a gate refusal. Product alone found that
README's "business code" is never reconciled with the gate's "governed files".
None of those is a restatement of another, and none came from the role that owns
the file they land in.

## The first attempt: built, not yet measured

Everything the milestone needs is built, tested and committed. The milestone's
**exit criterion has not been evaluated**, because the dogfooding run that would
evaluate it could not complete. Details below. `milestones.md` and
`roadmaps.md` read *In progress* for as long as that was true, and were flipped
to *Complete* only once the re-run produced a count.

Saying this plainly rather than declaring victory on the code is the point. The
milestone was never "write three agent files"; it was "find out whether three
independent agents notice things one model in three passes does not". The code
that can answer that question exists. The answer does not.

## What was built

| Piece | What it is |
|---|---|
| `agents/{product,dev,qa}.md` | The three roles, each drafting one contract file and returning a structured findings record |
| `schemas/findings.schema.json` | One role's findings, as an agent returns them |
| `schemas/run-summary.schema.json` | The counted overlap for one run |
| `src/amigos/findings.py` | Load, validate, key, count, write the run record |
| `amigos findings` | One command, three records, one atomic outcome |
| `skills/amigos/SKILL.md` | Eight phases became eight different phases: drafting, counting and reconciliation replace three sequential role passes plus a challenge round |

## The run that did not happen

The dogfooding run was `/amigos STORY-006` — the contract for v0.5's
`/implement`. It reached Phase 1 and stopped.

**All three drafting agents terminated on a session rate limit** before writing a
findings record. Not a bug in anything built here; the surrounding session ran
out of budget.

What makes it worth recording is what the system did next, because this was the
stop-the-run invariant firing on a real failure rather than in a test:

```text
$ amigos findings STORY-006 --product ... --dev ... --qa ...
error: .../findings-product.json: no findings record for the product role
exit 2

.amigos/runs                      does not exist - nothing was written
.amigos/stories/STORY-006/        the untouched scaffold, nothing more
state.json declared_state         amigos_running
```

Which is STORY-005's fifth scenario, word for word:

> Given one of the three agents returns no findings record
> When the reconciliation pass is reached
> Then the run stops before writing any contract file
> And state.json holds the declaration it carried before the drafting phase

The design anticipated a drafting agent returning nothing and specified that the
run must stop rather than reconcile from two. The first time that actually
happened, it stopped. That is one acceptance criterion demonstrated on live
failure instead of a fixture, which is worth more than the fixture.

`STORY-006` is left scaffolded and `amigos_running`. `amigos status` therefore
exits 1, and the milestone's closeout check does not pass — correctly, because
the milestone is not done. An empty story declaring a run in progress is an
accurate description of where this is.

## Two things this milestone could not test on itself

**Agent registration.** The three agent types were not addressable in the
session that created them — `Agent type 'product' not found`. The drafting
agents ran as fresh general-purpose agents that read their own role file from
`agents/*.md` as their first instruction.

That substitution preserves the property the milestone measures: a fresh agent
inherits no context, so the drafting is genuinely blind, and all three prompts
existed before any agent ran. It does not preserve packaging: whether
`.claude/agents/*.md` and the plugin's `"agents": "./agents"` actually register
is untested, exactly as v0.3 could not test skill discovery for the skill it had
just written. One difference from v0.3: the role restrictions in the agent
frontmatter (`tools: Read, Grep, Glob, Write`) are structural only when the agent
type is registered. Delivered as prompt text they are instructions, and a
general-purpose agent keeps Bash and Edit. The next session's run is the one that
tests this.

**Skill staleness.** Invoking `/amigos` loaded the **v0.3** text of `SKILL.md`,
not the v0.4 text sitting on disk — skills are snapshotted when the session
registers them, so a skill edited mid-session serves its old content. The run
followed the v0.4 file on disk instead. Worth knowing for any milestone that
edits a skill and then uses it: the edit is not live until something re-registers
it. The skill list did refresh later in the same session, so it is a lag rather
than a requirement to restart.

## Decisions taken during implementation

### The key excludes the target file, on purpose

Two findings are the same finding when they normalise to the same
`(target_section, risk_dimension)`. `target_file` is recorded on every finding
and deliberately left out of the key.

Including it would make the key more specific, produce fewer collisions, and
raise the count of findings named by exactly one role — which is the number this
design is judged on. A choice that biases a kill criterion should be resolved
toward the harder verdict, so the contract's literal wording wins: "the same
target section and the same risk dimension".

### One shared vocabulary, suggested rather than enforced

The measurement has a failure mode STORY-005 does not name: two roles noticing
the same risk in different words score as two unique findings, and the design
looks valuable because of vocabulary rather than perspective.

So all three agent files carry the same eight risk dimensions, word for word,
and `tests/test_agents.py` fails if they drift apart. This is not the *fixed*
vocabulary STORY-005's non-blocking question defers — the schema accepts any
string, and a coined dimension correctly counts as unique.

### Three records, one invocation

`amigos findings` takes all three paths at once rather than filing them one at a
time. There is then no intermediate state in which two records have been
accepted and a third is awaited, and therefore no state from which a
reconciliation could begin with two perspectives. The stop-the-run invariant is
structural rather than procedural.

### The run record lives outside the story directory

STORY-005 says the contract files are the only output of a run, and also that
the unique count is recorded for every run. Those read as a contradiction until
the seventh scenario settles it: "no commentary file is written into the story
directory". The prohibition is scoped to the story directory, so `.amigos/runs/`
is where evidence about a run belongs — beside the specification, not inside it.

### One deviation from the skill's letter

The skill says to spawn the three agents "in one batch". They were issued in
three consecutive calls instead. All three were in flight together and none
contained another's output, so the property held; the wording is stricter than
the requirement. Left as written, because the stricter phrasing is the safer
instruction to give a model.

## Verification results

```text
python -m pytest -q                                281 passed
amigos check STORY-005                             exit 0
amigos gate --staged                               permitted, STORY-005 (branch name)
scripts/findings.py READY-001 (fixture corpus)     9 findings, 6 distinct, 2 shared, 4 unique
scripts/findings.py STORY-006 (live failed run)    exit 2, nothing written
amigos status                                      exit 1 - STORY-006 amigos_running
```

The one line missing at the time was the one the milestone exists for:

```text
cat .amigos/runs/STORY-006/*/summary.json          does not exist
```

## Verification on the re-run

```text
python -m pytest -q                                281 passed
amigos check STORY-006                             exit 0, ready
amigos status                                      exit 0, all seven stories ready
amigos findings STORY-006 --product/--dev/--qa     50 findings, 30 distinct, 20 unique
cat .amigos/runs/STORY-006/*/summary.json          exists
```

## Follow-ups

- `tests/test_dogfooding.py` gains a case asserting a generated contract has a
  run record with a unique count. The evidence now exists, so the assertion is
  no longer asserting itself. The story list in that file is a literal tuple
  that omits STORY-006, so this is a governed edit needing its own ready story.
- The skill-staleness lag was not retested. `/amigos` served its on-disk v0.4
  text on this run, but the session had registered it before any edit, so the
  case that failed in v0.4 was not re-entered.
