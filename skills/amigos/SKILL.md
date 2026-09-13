---
name: amigos
description: Turn a ticket or feature request into a repository-local acceptance contract before implementation begins. Runs the Three Amigos perspectives - Product, Development, QA - over a story, challenges the result, and drives it to a deterministic Definition of Ready. Use when starting new work, when a story has no contract yet, when a contract needs revising, or when asked to run /amigos.
---

# Amigos: contract before implementation

Turn an under-specified request into a shared, explicit, testable contract.

**The output is the contract, not the conversation.** Nothing you discuss while
running this is an artifact. Only the files under `.amigos/stories/<id>/` are.

## What you may never do

These four hold for the whole run. Two of them are also refused by code; the
other two are only as strong as your discipline.

| Never | Why |
|---|---|
| Write or edit `dor.json` | Readiness is derived. A skill that writes it is judging itself. The validator is its only writer. |
| Declare `ready` or `blocked` in `state.json` | Those are computed. `amigos state` refuses both. |
| Invent an assumption to clear a blocking question | The blocker is the useful output. An invented answer is the failure this whole project exists to prevent. |
| Write a commentary, transcript or summary file into the story | Chat history is not authoritative. The contract is. |

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

Then read the repository: `README.md`, `docs/`, the components the request
touches, existing contracts under `.amigos/stories/`, and any tests or incidents
that bear on it. A contract written without reading the system is a guess.

## Phase 1 — Product

Own the question: **are we solving the right problem at the right scope?**

Determine the target user, the problem they have, the observable outcome that
should change, why it is worth doing now, and — the part most often skipped —
what is explicitly *out* of scope.

Do not: choose an architecture, invent requirements the request does not
support, or widen scope because adjacent functionality seems useful.

Draft `intent.md`. Every section filled; no `TODO` left anywhere.

## Phase 2 — Development

Own the question: **can this be built safely inside the existing system?**

Read the actual code before answering. Determine feasibility, the components
involved, real dependencies, the invariants that must survive, compatibility
constraints, and whether the story is too large and needs splitting.

Do not: widen the product scope, redefine success to make implementation
convenient, silently drop a requirement you find inconvenient, or freeze an
incidental implementation path into the contract. Constraints describe
boundaries and invariants, not the route you happen to have in mind.

Draft `constraints.md`.

## Phase 3 — QA

Own the question: **can two independent reviewers reach the same pass or fail?**

Write scenarios in Given-When-Then. Every scenario carries exactly one tag:

```gherkin
@primary
Scenario: The main path
  Given a relevant starting state
  When the action or event occurs
  Then an externally judgeable outcome holds

@counterexample
Scenario: A plausible nearby failure
  Given a relevant starting state
  When the action that should not succeed occurs
  Then the observable rejection holds
  And what must remain unchanged is named
```

At least one `@primary` and at least two `@counterexample`. Counterexamples
should cover *distinct* risk classes, not the same failure reworded.

**A `Then` must state something observable.** Not "the request is handled
correctly" but "the API returns HTTP 403 and no account data is modified". These
words make a clause unjudgeable and the linter rejects them:

```text
correct  correctly  appropriate  appropriately  reasonable  good
proper  properly  user-friendly  works  handled well  expected behavior
```

Before adding a scenario, check it earns its place: does removing it lose a real
failure class; is the `Then` decidable; does it constrain behaviour rather than
an execution path; is it distinct from the others; can you describe the nearby
failure it catches? Scenarios drawn from real incidents, complaints and
regressions come first.

Draft `acceptance.feature`.

## Phase 4 — Challenge

Now attack what you just wrote, from each perspective in turn. This is the phase
that makes the output more than one reading of the request.

- **Development challenges Product.** Which part of this scope is not buildable
  as described? What dependency is being assumed into existence? Should this be
  two stories?
- **QA challenges both.** Which `Then` cannot actually be judged? Which scenario
  restates another? Which stated behaviour has no scenario at all? What failure
  mode has nobody mentioned?
- **Product challenges the result.** Has the contract grown past the original
  problem? Is anything in scope that the request never asked for?

Every conflict resolves *into the contract* — a narrowed scope, an added
counterexample, a new invariant, or a blocking question. Never into a commentary
section.

## Phase 5 — Interview, at most twice

Only now, list what you genuinely could not determine and what would become an
invented assumption if you guessed. Typical: authorisation behaviour, what
happens to existing data, which error contract to reuse, contradictions between
source documents.

Ask the user, in **at most two rounds**, using multiple-choice questions where
you can. Ask only about things that change the contract.

Whatever is still unresolved goes into `open-questions.md` under `## Blocking`,
in the user's terms, as a question rather than a complaint. It will withhold
readiness through the ordinary check, which is the correct outcome.

Genuinely non-blocking questions go under `## Non-blocking` and do not stop the
story.

**Prefer a blocked story over invented certainty.** A blocked story is a working
result, not a failure of the run.

## Phase 6 — Synthesise

Write all four input files. Not `dor.json`, and not `state.json`.

## Phase 7 — Validate and repair, at most three attempts

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

## Phase 8 — Finish

```bash
amigos state <STORY-ID> --set draft --note "amigos run complete"
amigos check <STORY-ID>
```

Then report to the user, briefly:

- **ready** or **blocked**, and if blocked, the questions that stopped it;
- the scope you drew, especially what you put *out* of scope;
- conflicts the challenge phase surfaced and how each resolved;
- the scenarios you proposed, so a human reviews risk coverage rather than prose.

A human reviewer should be spending their attention on scope and risk. If they
have to rewrite your sections, the run did not work.
