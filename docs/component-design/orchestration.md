# Component Design: Contract Orchestration

The `/amigos` skill turns a story id and a description into a contract that
passes the Definition of Ready, or into a story that is explicitly blocked with
the questions that stopped it.

## The division of labour

```text
skill (a model)                 deterministic tools
  proposes a contract             decide whether it is one
  asks what it cannot determine   refuse what an agent may not declare
  repairs what was rejected       name the file, line and rule
  merges three drafts             count what only one role found
```

The model never judges its own output. `amigos check` decides readiness and
`dor.json` has one writer that is not the skill; `amigos findings` decides what
the three roles actually contributed, and the skill does not get to summarise
that in its own favour.

## Phases

| Phase | Does |
|---|---|
| 0 Set up | create or reopen; declare `amigos_running`; write the ticket |
| 1 Draft | three agents, same ticket, none sees another's output |
| 2 Count | `amigos findings`; what did exactly one role notice? |
| 3 Reconcile | merge the drafts; every conflict resolves into the contract |
| 4 Interview | at most two rounds, only on what would become an assumption |
| 5 Synthesise | write the four input files |
| 6 Validate | `amigos check`, repair, re-check, at most three attempts |
| 7 Finish | return to `draft`; report ready or blocked, with the count |

`amigos_running` withholds readiness for the whole run, so a half-written
contract can never read as ready to anything downstream — including the gate.

## Blind drafting

Three agents receive the same ticket and the same repository access. None
receives another's output.

Independence has to be structural, because instructional independence is cheap
to claim and impossible to verify: an agent told to ignore what it has read has
still read it. Two rules make it structural.

- Each role is spawned as its own agent type, never as a fork of the
  orchestrator. A fork inherits the orchestrator's conversation, which by the
  drafting phase contains the ticket, the orchestrator's reading of it, and
  shortly the other roles' drafts.
- All three prompts are assembled before any agent runs, so no prompt can
  contain an output that does not exist yet.

Each agent returns its draft and writes a findings record. Drafts do not go into
the story directory; only the reconciliation pass writes contract files.

## Counting what the split bought

The Three Amigos split costs three agent invocations per run. Whether it earns
them is a question with an answer, and `amigos findings` computes it.

Two findings are the same finding when they normalise to the same
`(target_section, risk_dimension)` pair. `target_file` is deliberately excluded:
including it would produce fewer collisions and a larger count of findings named
by exactly one role, which is the number the design is judged on. Where a choice
biases a kill criterion, take the one that makes it harder to pass.

The three agent definitions therefore carry the **same** suggested risk
dimensions, word for word. Free-text vocabulary would let two roles notice the
same risk in different words and score as two separate findings, flattering the
design with nothing but word choice. `tests/test_agents.py` fails if the three
lists drift apart.

A count of zero is a result, not an error. The command says so in as many words,
and a run that reports it is the kill criterion firing.

A missing, malformed or empty findings record stops the run. All three records
are passed to one invocation, so there is no intermediate state in which two have
been accepted and a third is awaited — and therefore no state from which a
reconciliation could begin with two perspectives.

## The run record

```text
.amigos/runs/<STORY-ID>/<run-id>/
├── findings/{product,dev,qa}.json
└── summary.json
```

Outside the story directory, because the story directory is the specification a
downstream agent reads and this is evidence about how that specification was
produced. Runs accumulate rather than overwrite: a count that survives only until
the next run cannot be compared to anything.

Committed, because README section 30 makes the repository the evidence. A count
that exists only in a conversation is not recorded, by this project's own
definition of what an artifact is.

## The two bounds

**The interview is bounded at two rounds.** README section 24 prefers `blocked`
over invented certainty; section 23 says the system should surface uncertainty
rather than make humans rewrite artifacts by hand. Asking first and blocking
second satisfies both, in that order. An agent required to reach zero blockers
has an incentive to accept a weak answer, which is how invented certainty gets
in.

**The repair loop is bounded at three attempts.** A drafting agent that writes
once and stops hands back contracts that fail their own validator, leaving the
repair to a human — the work this project exists to remove. An unbounded loop
against a rule the model has not understood is the opposite failure: it burns
budget and ends in the same place. On exhaustion the skill reports the remaining
findings and leaves the story in `draft`, claiming neither success nor blockage.

## What the skill may not do

| Never | Enforced by |
|---|---|
| Write or edit `dor.json` | code — the validator is its only writer |
| Declare `ready` or `blocked` | code — `amigos state` and `read_state` both refuse |
| Put one role's work into another role's prompt | partly code — a fresh agent inherits no context; the orchestrator can still paste |
| Invent an assumption to clear a blocker | the instructions, and review |
| Write a commentary or transcript file into the story | the instructions, and review |

Some of these are refused by code rather than by the skill remembering them. The
rest are only as strong as the instructions and the reviewer, which is stated
plainly rather than implied.

The third is the interesting one: spawning a fresh agent structurally prevents
context inheritance, but nothing stops an orchestrator from pasting one draft
into another prompt. `tests/test_skill.py` holds the line it can — every mention
of forking in the skill must be a prohibition — and the rest is review.

## Repairing without hollowing out

The failure mode worth naming: a repair loop pointed at a validator will find
the cheapest way to satisfy it. Deleting a counterexample satisfies a count.
Removing an assertion satisfies the lint.

The lint is built so this does not pay — it rejects unjudgeable *wording*, not
content, so the cheapest way to pass is to state the observable outcome. The
skill says so explicitly. It remains something a reviewer should look for.

## Placement

```text
skills/amigos/SKILL.md      the plugin's copy, declared in plugin.json
agents/{product,dev,qa}.md  the three roles, declared in plugin.json
.claude/skills/amigos       a symlink, so this checkout dogfoods the same file
.claude/agents/*.md         symlinks, for the same reason
```

One file per thing, two discovery paths, no second copy to drift.
`tests/test_skill.py` and `tests/test_agents.py` assert every symlink resolves to
the shipped file rather than a duplicate.

## Held to the code

A prompt cannot be unit tested for behaviour, but it can be held to the rules the
code enforces. `tests/test_skill.py` and `tests/test_agents.py` fail when the
instructions drift: if the skill names a command that does not exist, a lifecycle
state that is not declarable, a Definition of Ready check the validator does not
compute, if an agent's example findings record would be rejected by the schema,
if the three risk vocabularies stop matching each other, or if the vague-word
list in the QA agent stops matching the one the linter uses.

The last two matter most. An agent teaching a model to write clauses the linter
rejects would make the repair loop do work that never needed doing. Three
vocabularies that drifted apart would keep producing counts, and the counts would
mean nothing, and nothing else in the system would notice.
