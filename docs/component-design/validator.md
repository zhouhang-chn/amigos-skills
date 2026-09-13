# Component Design: The Deterministic Validator

## Modules

```text
config.py      .amigos/config.json plus defaults
gherkin.py     the supported Gherkin subset, with line numbers
markdown.py    level-2 sections, list items, placeholder detection
lint.py        acceptance criteria rules
dor.py         the seven checks, state derivation, dor.json generation
story.py       story paths, scaffolding, state.json
jsonschema.py  in-tree schema checking, no dependency
cli.py         init | create | check | lint | status
```

`dor.py` consumes `lint.py` as a library. There is one implementation of each
rule, surfaced through two commands.

## The seven checks

Names are README section 5's, verbatim.

| Check | Rule |
|---|---|
| `intent_defined` | User, Problem and Desired Outcome present and non-placeholder |
| `scope_defined` | In Scope and Out of Scope each list at least one bullet |
| `constraints_defined` | at least one constraints section lists a bullet |
| `primary_scenario_present` | `@primary` count ≥ `dor.min_primary` |
| `counterexamples_present` | `@counterexample` count ≥ `dor.min_counterexamples` |
| `assertions_are_determinable` | the acceptance lint reports no failure |
| `blocking_questions_resolved` | no bullets under `## Blocking` |

## Lint rules

| Rule | Severity | Fires on |
|---|---|---|
| `vague-assertion` | failure | README section 17 vocabulary in an assertion |
| `missing-then` | failure | a scenario with no `Then` |
| `empty-step` | failure | a step keyword with no text |
| `untagged-scenario` | failure | a scenario with no role tag |
| `ambiguous-tag` | failure | a scenario with both role tags |
| `then-before-when` | warning | an assertion preceding the action it judges |

Vocabulary matching is case-insensitive and bounded to whole words, so
`incorrectness` does not fire on `correct`. Multi-word entries match across any
run of whitespace. Only `Then` steps and the `And` or `But` steps continuing one
are scanned: `Given` and `When` describe setup, not assertions.

There is no per-line suppression comment. README section 31 says not to build
the escape hatch before a rule has been shown to be wrong.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | ready |
| 1 | evaluated, not ready |
| 2 | structurally unusable, or a usage error |

The separation matters for the repository gate: code 1 is a contract that needs
more work, code 2 is a contract the validator could not read at all.

`amigos status` reports the worst outcome across every story.

### Structural, not merely failing

These raise rather than producing a verdict, and **no `dor.json` is written**:

- a missing story directory, or a missing contract input file;
- `state.json` malformed, or declaring `ready` or `blocked`;
- `acceptance.feature` outside the supported Gherkin subset;
- a scenario tagged with neither or both roles, so role counts are undefined;
- a generated payload that would not satisfy `dor.schema.json`.

Recording a readiness judgement about an input the validator could not read
would be worse than recording nothing.

## Determinism

Two runs over unchanged files produce identical checks, identical failures and
identical exit codes. The single volatile field in `dor.json` is `generated_at`,
which `tests/test_dogfooding.py` excludes when comparing a committed record
against a fresh evaluation.

`contract_hash` records SHA-256 of each input file. Nothing reads it in v0.1; it
is the baseline the contract-immutability enforcement of a later milestone will
diff against, and it costs nothing to start recording now.
