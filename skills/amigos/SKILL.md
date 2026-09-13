---
name: amigos
description: Turn a ticket or feature request into a repository-local acceptance contract before implementation begins. Runs the Three Amigos perspectives - Product, Development, QA - as three independent agents that draft blind, counts what each of them found that the others did not, reconciles the three drafts, and drives the result to a deterministic Definition of Ready. Use when starting new work, when a story has no contract yet, when a contract needs revising, or when asked to run /amigos.
---

# Amigos: contract before implementation

Turn an under-specified request into a shared, explicit, testable contract.

**The output is the contract, not the conversation.** Nothing you discuss while
running this is an artifact. Only the files under `.amigos/stories/<id>/` are.

## What you may never do

These five hold for the whole run.

| Never | Why | Held by |
|---|---|---|
| Write or edit `dor.json` | Readiness is derived. A skill that writes it is judging itself. The validator is its only writer. | you |
| Declare `ready` or `blocked` in `state.json` | Those are computed. `amigos state` refuses both. | code |
| Put one role's work into another role's prompt during drafting | Independence that exists only in the instructions is not independence. Three perspectives that have read each other become one perspective stated three times. | you, and by spawning fresh agents rather than forks |
| Invent an assumption to clear a blocking question | The blocker is the useful output. An invented answer is the failure this whole project exists to prevent. | you |
| Write a commentary, transcript or summary file into the story directory | Chat history is not authoritative. The contract is. | you |

## Phase 0 — Set up

```bash
amigos check <STORY-ID>          # does a contract already exist?
```

**New story** (the check reports the story is not found):

```bash
amigos create <STORY-ID>
amigos state <STORY-ID> --set amigos_running --note "<why this story exists>"
```

**Existing story** being revised:

```bash
amigos state <STORY-ID> --set contract_change --note "<what prompted the change>"
```

`amigos_running` and `contract_change` both withhold readiness while you work,
so a half-written contract can never read as ready to anything downstream.

Then write **the ticket**: the request, in one block of text, with everything you
were told and nothing you have concluded. All three drafting agents receive this
same text. A difference in what they find must be a difference in perspective,
not a difference in what they were handed.

Do not read the repository yourself in order to pre-digest it for them. They
read it; that is the job.

## Phase 1 — Draft blind

Spawn **three agents, in one batch, before any of them has returned**:

| Agent type | Owns | Drafts |
|---|---|---|
| `product` | Are we solving the right problem at the right scope? | `intent.md` |
| `dev` | Can this be built safely inside the existing system? | `constraints.md` |
| `qa` | Can two independent reviewers reach the same pass or fail? | `acceptance.feature` |

Each prompt contains: the story id, the ticket verbatim, and a path in a scratch
directory **outside the repository** where that agent writes its findings record
(`<scratch>/findings-product.json`, `-dev`, `-qa`).

Two rules make the independence structural rather than polite:

- Spawn each as its own agent type. **Never as a fork** — a fork inherits this
  conversation, which by now contains the ticket, your reading of it, and
  shortly the other roles' drafts.
- Assemble all three prompts before any agent runs, so no prompt can contain an
  output that does not exist yet.

Each agent returns its draft in its final message and writes its findings
record to the path you gave it.

## Phase 2 — Count the overlap

```bash
amigos findings <STORY-ID> \
  --product <scratch>/findings-product.json \
  --dev     <scratch>/findings-dev.json \
  --qa      <scratch>/findings-qa.json
```

This is the only place the value of the split is measured, and it is measured by
code. Two findings are the same finding when they carry the same target section
and the same risk dimension; the command reports how many findings exactly one
role named.

**If it exits non-zero, the run stops here.** A missing, malformed or empty
findings record means a perspective is missing, and a contract reconciled from
the remaining two is not a Three Amigos contract. Report what the command said
and leave the story where it is — the state declared in Phase 0 still stands,
which is exactly what should happen.

A count of zero is not a failure. It is a result: nobody found anything the
others missed. Report it as it is.

## Phase 3 — Reconcile

You now hold three drafts written without reference to each other, and a list of
what each role found. Merge them into one contract.

Where the roles conflict, the conflict is the most valuable thing in the run.
Read the drafts against each other and look for it:

- **Development against Product.** Which part of this scope is not buildable as
  described? What dependency is being assumed into existence? Should this be two
  stories?
- **QA against both.** Which `Then` cannot actually be judged? Which scenario
  restates another? Which stated behaviour has no scenario at all?
- **Product against the result.** Has the contract grown past the original
  problem? Is anything here that the request never asked for?

**Every conflict resolves into the contract** — a narrowed scope, an added
counterexample, a new invariant, or a blocking question. Never into a commentary
section, and never by preferring the role that wrote more fluently.

A finding you decide not to act on is a decision. Record it where it belongs: an
`## Out of Scope` entry with its reason, or a `## Non-blocking` question. Do not
drop it silently — it is in the run record, and a reviewer can see you did.

## Phase 4 — Interview, at most twice

Only now, list what you genuinely could not determine and what would become an
invented assumption if you guessed. Typical: authorisation behaviour, what
happens to existing data, which error contract to reuse, contradictions between
source documents. The roles' findings records are the shortlist.

Ask the user, in **at most two rounds**, using multiple-choice questions where
you can. Ask only about things that change the contract.

Whatever is still unresolved goes into `open-questions.md` under `## Blocking`,
in the user's terms, as a question rather than a complaint. It will withhold
readiness through the ordinary check, which is the correct outcome.

Genuinely non-blocking questions go under `## Non-blocking` and do not stop the
story.

**Prefer a blocked story over invented certainty.** A blocked story is a working
result, not a failure of the run.

## Phase 5 — Synthesise

Write all four input files. Not `dor.json`, and not `state.json`.

```text
intent.md            constraints.md
acceptance.feature   open-questions.md
```

Nothing else goes into the story directory.

## Phase 6 — Validate and repair, at most three attempts

```bash
amigos check <STORY-ID>
```

The validator names the failing check, the file and the line. Fix what it found
and run it again. **At most three attempts.**

Fix the contract, never the assertion's meaning. If the linter rejects wording,
state the observable outcome — do not delete the assertion to make the check
pass. Removing a counterexample to satisfy a count is the same failure wearing a
different hat.

If three attempts do not converge, stop. Report the remaining findings verbatim
and leave the story in `draft`. Do not keep retrying a rule you have not
understood.

## Phase 7 — Finish

```bash
amigos state <STORY-ID> --set draft --note "amigos run complete"
amigos check <STORY-ID>
```

Then report to the user, briefly:

- **ready** or **blocked**, and if blocked, the questions that stopped it;
- the scope you drew, especially what you put *out* of scope;
- **what each role found that the others did not** — the count from Phase 2, and
  one example per role. If the count was zero, say so plainly: on this run the
  split bought nothing;
- conflicts between the roles and how each resolved;
- the scenarios you proposed, so a human reviews risk coverage rather than prose.

A human reviewer should be spending their attention on scope and risk. If they
have to rewrite your sections, the run did not work.
