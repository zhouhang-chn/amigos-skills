# v0.4 Independent Subagents — Design

Story: **STORY-005**.

## The shape of a run

```text
/amigos STORY-123 "a description"

  Phase 0   set up, declare amigos_running
  Phase 1   BLIND DRAFTING
                +----------------+----------------+
                |                |                |
                v                v                v
             product            dev               qa
             agent             agent             agent
                |                |                |
        intent.md draft   constraints draft   feature draft
        findings record   findings record   findings record
                |                |                |
                +----------------+----------------+
                                 |
  Phase 2                  amigos findings        <- code, not a model
                                 |
                        overlap counted, run record written
                                 |
  Phase 3                 RECONCILIATION           <- the orchestrator
                                 |
                        the four contract files
                                 |
  Phase 4..6      interview, validate, repair, finish (unchanged)
```

The three drafting agents replace v0.3's Phases 1–3. Everything from the
interview onwards is v0.3's, unchanged.

## Blind drafting

Each role is a separate subagent invocation that starts with **no** inherited
context. Independence has to be structural, not instructional: an agent told
"ignore what you have read" has still read it.

Three rules make it structural:

1. A drafting agent is spawned as its own agent type (`product`, `dev`, `qa`),
   never as a fork of the orchestrator. A fork inherits the orchestrator's
   conversation, which by Phase 1 already contains the other roles' work.
2. The three prompts are assembled before any agent runs, so no prompt can
   contain an output that does not exist yet.
3. All three receive the same ticket text and the same repository access, so a
   difference in their findings is a difference in perspective rather than a
   difference in information. This is STORY-005's own constraint.

Each agent returns its draft in its final message and writes its findings record
to a path supplied in its prompt. Drafts do not go into the story directory:
only the reconciliation pass writes contract files.

## The findings record

One JSON file per role. Structured, because the whole point is that overlap is
computed rather than judged.

```json
{
  "schema_version": 1,
  "story_id": "STORY-123",
  "role": "product",
  "findings": [
    {
      "target_file": "intent.md",
      "target_section": "In Scope",
      "risk_dimension": "scope",
      "statement": "The ticket does not say whether existing sessions are revoked."
    }
  ]
}
```

`role`, `target_file`, `target_section` and `risk_dimension` are the four the
contract names. `statement` is required on top of them: a finding that names a
location and a dimension but does not say what was found is a coordinate, not a
finding. `role` may also be repeated on an individual finding, and must then
agree with the record's — every finding in the stored run record carries its
role, as the contract's second scenario requires.

An empty `findings` array is a structural failure, not an empty result. A role
with nothing to say about an under-specified ticket has not done its job, and
the contract's first invariant says the run stops rather than producing a
contract from the remaining two.

Schema: `schemas/findings.schema.json`, checked with the existing in-tree
checker, so the run record is validated the same way `dor.json` is.

## Counting overlap

Two findings are **the same finding** when they normalise to the same
`(target_section, risk_dimension)` pair. Normalisation is lowercase, trimmed,
internal whitespace collapsed, and a leading `#` run stripped so `## In Scope`
and `In Scope` are one section.

The key is the contract's wording taken literally:

> Given two roles that name the same target section and the same risk dimension

`target_file` is deliberately **not** part of the key. Including it would make
the key more specific, produce fewer collisions, and inflate the count of
findings named by exactly one role — which is the number that decides whether
this milestone survives. Where a choice biases a kill criterion, take the one
that makes the criterion harder to pass. In practice the two readings almost
always coincide, because section names in this contract format are already
distinct across the four files.

From the keyed set:

```text
distinct   number of distinct keys
shared     keys named by more than one role
unique     keys named by exactly one role       <- the number that matters
```

`unique == 0` is a legitimate, reportable outcome, not an error. It is the
milestone's kill signal, and a run that produced it must say so in its own
words. The text output prints, verbatim:

```text
No role contributed a finding the others missed.
```

## Why a shared dimension vocabulary

Free-text dimensions would make the measurement worthless in the direction that
flatters the design: two roles noticing the same risk in different words score
as two unique findings.

So all three agent definitions carry the **same** eight dimensions, word for
word, with "use one of these if it fits; invent one only if none does":

```text
ambiguity       a statement two careful readers would read differently
scope           something in or out that the request does not settle
feasibility     something that cannot be built as described in this system
dependency      something assumed to exist that may not
invariant       something that must keep holding and is not written down
testability     an outcome nobody can judge from outside
coverage        a behaviour or failure mode with no scenario
compatibility   something that breaks an existing caller, file or contract
```

This is the same principle as the contract's own constraint — same ticket, same
repository access, so a difference is a difference in perspective — applied to
the output side. A difference in dimension should mean the roles judged
differently, not that they reached for different words.

It is not the *fixed* vocabulary STORY-005's non-blocking question defers. The
list is suggested in the prompts and unenforced by the schema: a role may coin a
dimension, and that coinage will correctly count as unique. A test asserts the
three agent files carry an identical list, because the moment they drift the
counts stop meaning anything and nothing else would notice.

## `amigos findings`

One command, one invocation, all three records at once:

```bash
amigos findings STORY-123 --product p.json --dev d.json --qa q.json
```

| Exit | Meaning |
|---|---|
| 0 | Three valid records; the run record and summary are written. |
| 2 | A record is missing, malformed, empty, or names the wrong story or role. Nothing is written. |

Taking all three paths in one call is what makes the stop-the-run invariant real
rather than procedural. There is no state between calls in which two records
have been accepted and a third is being waited for, so there is no state from
which a reconciliation could begin with two.

There is no exit code 1. Every other command in this project uses 1 for "valid
input, unsatisfactory result", and this command has no such outcome: a zero
unique count is a result the summary reports, not a failure.

## The run record

```text
.amigos/runs/<STORY-ID>/<run-id>/
├── findings/
│   ├── product.json
│   ├── dev.json
│   └── qa.json
└── summary.json
```

`<run-id>` is a UTC timestamp, so runs accumulate rather than overwrite. The
contract asks for the count to be recorded for **every** run.

**Why outside the story directory.** STORY-005 says the contract files remain
the only output of a run, and also that the unique count is recorded for every
run. Those read as a contradiction until the acceptance criteria are consulted;
the seventh scenario resolves it:

> And no commentary file is written into the story directory

The prohibition is scoped to the story directory. `.amigos/runs/` is evidence
about a run, not part of the specification a downstream agent reads — the same
relationship `dor.json` has to readiness, kept one directory further away
because nothing downstream consumes it. `.amigos/stories/<id>/` still holds
exactly the five inputs and `dor.json`.

The run record is committed. README section 30 makes the repository the evidence;
a count that exists only in a conversation is not recorded, by this project's own
definition of what an artifact is.

`summary.json`:

```json
{
  "schema_version": 1,
  "story_id": "STORY-123",
  "run_id": "2026-09-13T10-42-11Z",
  "generated_at": "2026-09-13T10:42:11Z",
  "generator": "amigos 0.4.0",
  "findings_by_role": { "product": 7, "dev": 6, "qa": 9 },
  "total_findings": 22,
  "distinct_findings": 18,
  "shared": 4,
  "unique": 14,
  "unique_by_role": { "product": 5, "dev": 4, "qa": 5 },
  "split_added_nothing": false,
  "keys": [
    { "target_section": "in scope", "risk_dimension": "scope",
      "roles": ["product", "qa"], "shared": true,
      "sources": [ { "role": "product", "target_file": "intent.md", "...": "..." } ] }
  ]
}
```

## Agent definitions

```text
agents/
├── product.md
├── dev.md
└── qa.md
```

One file per role, with frontmatter naming the agent and describing when to use
it. Responsibilities and prohibitions come from README sections 10–12 verbatim,
minus one change the contract forces: sections 11 and 12 list "Product output"
and "Development output" among the inputs, which blind drafting removes. README
is amended rather than contradicted.

Discovery follows the v0.3 pattern exactly: `agents/` is the plugin's copy,
`.claude/agents/*.md` are symlinks to it, and a test asserts each link resolves
to the shipped file. Three milestones running, the right answer has been to
delete the second copy rather than keep two in sync.

`.claude-plugin/plugin.json` gains `"agents": "./agents"`, declared now that the
directory exists and not before.

## `skills/amigos/SKILL.md`

Phases 1–3 become one drafting phase plus a counting phase plus a reconciliation
phase. The bounds and the four prohibitions are unchanged, and one prohibition is
added for the drafting phase: **do not pass a role's output to another role.**

The reconciliation pass is the orchestrator's own work. It holds the three
drafts and the summary, and writes the four files. Where roles conflict, the
conflict resolves into the contract — a narrowed scope, an added counterexample,
a new invariant, or a blocking question — never into commentary. That rule is
v0.3's Phase 4 language, moved to where the conflicts now actually arise.

## Tests

A prompt cannot be unit tested for what a model will do with it, so the tests
hold the prompts to what the code enforces, as v0.3's do:

| Test | What breaks it |
|---|---|
| Overlap counting, over hand-built records | A key that merges or splits wrongly |
| `unique == 0` reports the exact sentence | Silent success when the split adds nothing |
| An empty or missing record exits 2 and writes nothing | The stop-the-run invariant becoming procedural |
| A record naming the wrong story or role exits 2 | Cross-run contamination |
| The three agent files carry an identical dimension list | Vocabulary drift making counts meaningless |
| Each agent file names only real files, states and commands | An agent instructed to use something that does not exist |
| `.claude/agents/*` resolve to the shipped files | A duplicate copy drifting from the plugin's |
| The skill's drafting phase never names a fork | Blind drafting quietly becoming inherited context |

Plus the dogfooding tests: the contract this milestone generates must pass the
same validator, and its run record must exist and carry a unique count.

## Alternatives considered

**Three phases in one context with stronger instructions.** Cheaper by three
agent invocations. Rejected because it is the thing v0.4 exists to test against;
instructional independence is what v0.3 already had.

**Forked subagents.** A fork inherits the orchestrator's context, which is the
one thing blind drafting forbids. Rejected outright, and a test guards it.

**Model-judged overlap.** Ask a model which findings are the same. Rejected: the
project's entire thesis is that the decision worth trusting is the one code
makes. A model-judged kill criterion is an opinion with a number printed on it.

**Findings records in the story directory.** Rejected by the contract's seventh
scenario, and independently by taste: the story directory is the specification,
and a downstream agent reading it should not have to tell evidence from spec.

**Per-run overwrite instead of timestamped runs.** Cheaper on disk, and loses
the comparison across runs that STORY-005's deferred vocabulary question needs
to be answerable at all.
