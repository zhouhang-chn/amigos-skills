# Component Design: The `.amigos/` Contract Protocol

`.amigos/` is the protocol. Claude Code and Codex are execution environments.
Nothing under `.amigos/` may depend on either.

## Layout

```text
.amigos/
├── config.json
└── stories/
    └── <STORY-ID>/
        ├── intent.md            input, hand- or agent-authored
        ├── constraints.md       input
        ├── acceptance.feature   input
        ├── open-questions.md    input
        ├── state.json           input, agent-owned lifecycle
        └── dor.json             output, validator-owned
```

Story IDs start with a letter and continue with letters, digits, dot, underscore
or hyphen. They are local strings with no external synchronisation.

## Ownership

The split between `state.json` and `dor.json` is the mechanism behind
"deterministic gates over self-evaluation".

| File | Writer | Carries |
|---|---|---|
| `state.json` | agents and humans | the declared lifecycle state |
| `dor.json` | the validator, only | every check, `ready`, the effective state |

`state.json.declared_state` accepts `draft`, `amigos_running` and
`contract_change`. It does **not** accept `ready` or `blocked`: those are
computed, and an attempt to declare one is a structural error, not a warning.
That refusal is the load-bearing part of the design — without it, the model that
drafted a contract could also grant it readiness.

`declared_state` can only ever withhold readiness, never grant it:

```text
declared amigos_running or contract_change  →  that state, ready = false
otherwise, a check fails or a blocker is open →  blocked,     ready = false
otherwise                                     →  ready,       ready = true
```

`draft` therefore means "no lifecycle event recorded", not "unfinished".
Readiness is a property of the contract's content.

## Section headings

Headings are matched case-insensitively at level two. A section whose body is
blank, or still carries scaffolding text (`TODO`, `<!-- amigos:placeholder -->`),
counts as absent. "The file exists" is never enough to satisfy a check.

| File | Headings read |
|---|---|
| `intent.md` | User, Problem, Desired Outcome, In Scope, Out of Scope |
| `constraints.md` | Technical Constraints, Dependencies, Invariants, Relevant Components |
| `open-questions.md` | Blocking |

`In Scope` and `Out of Scope` must list at least one bullet each. `- None` is an
acceptable bullet; an empty section is not, because declining to state what is
out of scope is the omission that lets scope expand later.

Under `Blocking`, bullets are blocking questions. Prose such as `None.` is not a
bullet and so leaves no blockers open.

## Gherkin subset

`acceptance.feature` uses a deliberately small subset. A construct outside it is
a parse error rather than something skipped, because a construct the validator
ignores is a route through which an unjudgeable assertion reaches a ready
contract.

Supported: one `Feature`; an optional `Background`; `Scenario` and
`Scenario Outline` with `Examples`; tag lines; `Given`, `When`, `Then`, `And`,
`But`; `#` comments; triple-quoted doc strings; pipe-delimited data tables.

Not supported: `Rule:`, the `*` step keyword, more than one `Feature`, a
`Scenario Outline` without `Examples`, tags on a `Background`.

`And` and `But` inherit the keyword they continue, so an `And` after a `Then` is
an assertion and an `And` after a `Given` is not. Only assertions are scanned for
vocabulary.

### Scenario roles

Every scenario carries exactly one of `@primary` or `@counterexample`. This is
what makes "at least one primary path and at least two counterexamples"
decidable by a script rather than inferred from wording. A scenario carrying
neither or both is a structural error: the counts cannot be computed, so no
verdict is produced.

Other tags are permitted and ignored.

## Configuration

```json
{
  "schema_version": 1,
  "stories_dir": ".amigos/stories",
  "lint": { "vague_words_extra": [], "vague_words_remove": [] },
  "dor": { "min_primary": 1, "min_counterexamples": 2 }
}
```

Every key is optional. A repository may extend or shorten the lint vocabulary
but cannot disable the rule set.

## Schemas

`schemas/dor.schema.json` and `schemas/state.schema.json`. `dor.json` is
validated against its schema every time it is written; a payload that would not
validate is not written at all.
