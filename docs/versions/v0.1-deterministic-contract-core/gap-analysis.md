# v0.1 Deterministic Contract Core — Gap Analysis

## Current state at kickoff

The repository contained `README.md` and `docs/amigos-skills.png`. Nothing
executable, no contract format on disk, no stories.

## Gaps

| Gap | Severity | Impact |
|---|---|---|
| No on-disk contract format | High | Every agent invents its own file names and headings; no tool can judge a contract. |
| Readiness decided by model judgement | High | The gate measures the drafting model's confidence rather than the contract's quality. |
| No signal distinguishing a primary path from a counterexample | High | README's "at least two counterexamples" is undecidable by a script. |
| Vague assertions undetectable | High | "Then the result is handled correctly" passes any review that is not looking for it. |
| No way to scaffold a story | Medium | The format would be transcribed by hand and drift immediately. |

## Contradictions found in README.md

Recorded here because they had to be resolved before anything could be built.

1. **`dor.json` ownership.** Section 5 lists it as a contract artifact written
   beside `intent.md`; section 16 says readiness must be verified by code;
   section 21 lists both `check_dor.py` and `generate_dor.py`. If the drafting
   model writes `dor.json` and a script only schema-validates it, the model is
   still the judge.
2. **`state` is not derivable.** `dor.json` carries both `state` and `ready`.
   `ready` and `blocked` are computable; `amigos_running` and `contract_change`
   are lifecycle events with no assigned writer.
3. **Counterexamples have no deterministic signal.** Nothing in a `.feature`
   file says which scenario is a counterexample.
4. **Contract immutability has no mechanism.** Sections 14 and 29 require
   detecting that `/implement` edited `acceptance.feature`, with nothing
   recorded to compare against.
5. **Section 20's Codex tree is malformed.** Cosmetic, but it indicates Codex
   support was sketched rather than designed.

## Non-goals for this milestone

`/amigos`, `/implement`, subagents, enforcement hooks, the Codex mirror, eval
export, contract diffing, external trackers.

## Open questions

None blocking. Carried forward: whether `then-before-when` should become a
failure, and whether `min_counterexamples` should be settable per story.
