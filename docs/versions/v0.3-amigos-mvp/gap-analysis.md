# v0.3 `/amigos` MVP — Gap Analysis

## Current state

The contract format exists, readiness is computed deterministically, and the
gate refuses governed changes without a ready story. Every contract so far has
been written by hand. The framework cannot yet produce the artifact it exists to
produce.

## Gaps

| Gap | Severity | Impact |
|---|---|---|
| Contracts are hand-authored | High | The project demonstrates a format, not a capability. Nothing has tested whether an agent can produce a contract that passes a gate it did not write. |
| No Three Amigos process, only its output shape | High | The three perspectives exist as headings in a template. Nothing makes a drafting agent actually take them. |
| No repair loop between drafting and validation | Medium | An agent that drafts once and stops will routinely hand back contracts that fail their own validator, and a human ends up doing the repair. |
| Nothing can set the lifecycle state | Medium | `state.json` is written once by scaffolding and never again, so `amigos_running` and `contract_change` are unreachable in practice. |
| Missing information has no route to a human | Medium | The protocol can record a blocking question but has no moment at which one gets asked. |

## Non-goals for this milestone

- Independent Product, Development and QA subagents. README section 32 puts one
  orchestrating model here and splits the roles in v0.4, so that v0.4 has a
  baseline to prove itself against.
- `/implement`. Consuming a contract is v0.5.
- The full contract-change workflow with diffs and reapproval. Reopening a story
  is in scope; formalising the change event is Phase 8.
- Any external ticket source. The story id and a free-text description are the
  input.

## The last hand-authored contract

STORY-004 is written by hand, because the thing that would write it is the thing
it specifies. README section 28 makes this the handoff point:

> After `/amigos`: new story contracts must be generated through `/amigos`.

From the end of this milestone, hand-authoring a contract becomes the exception
that needs a reason. The milestone is not complete until `/amigos` has produced
a real contract for the next story.

## Open questions

None blocking. Settled at kickoff and recorded in [design.md](design.md): a
bounded interview before blocking, a skill that drives deterministic tools with
a repair loop, and three drafting passes plus one challenge pass.

Carried forward: whether the challenge pass earns its cost, which is a question
v0.4 answers with evidence rather than argument.
