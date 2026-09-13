# v0.1 Deterministic Contract Core — Implementation Notes

## Decisions taken during implementation

### Structural defects produce no `dor.json`

Surfaced while hand-authoring STORY-001. Writing a readiness record about an
input the validator could not read would put a file on disk asserting something
the validator never established. The fourth scenario of STORY-001 fixes this in
the contract: `Then dor.json is not written`.

Consequence: exit code 2 means "unreadable", exit code 1 means "read and not
ready". The repository gate in v0.2 needs that distinction.

### `contract_change` withholds readiness too

The kickoff plan only had `amigos_running` withholding readiness. Writing the
protocol down made the omission obvious: `contract_change` means the contract is
under revision, and its checks may all still pass from the previous version. A
story under revision that reports `ready` would let implementation proceed
against a contract being rewritten underneath it. Both states now withhold.

### One defect, one finding

An empty `Then` fires `empty-step` and deliberately does not also fire
`missing-then`. Two findings for one defect makes a report harder to act on. The
first test written for this asserted both; the test was wrong, not the code.

### `amigos status` reports the worst outcome

A repository holding one unreadable story exits 2 even if every other story is
ready, because the unreadable one is the more urgent fact. Again, the first test
expected 1; the behaviour is right and the expectation was corrected.

### Two modules beyond the plan

`markdown.py` and `jsonschema.py` were not named at kickoff. `markdown.py`
separates placeholder detection from the checks that depend on it.
`jsonschema.py` exists because STORY-002's invariant requires `dor.json` to
validate against its schema on every write, and a runtime dependency would break
the promise that the gate runs anywhere without an install step. It implements
only the keywords the two schemas use and raises on any keyword it does not,
so a schema cannot quietly go unchecked.

## Dogfooding evidence

### The Phase 0 to Phase 1 handoff test

STORY-001, STORY-002 and STORY-003 were written before any validator existed,
then evaluated by the validator built afterwards. All three passed with no edits
to the contracts.

This is encouraging but weak evidence: the same author wrote the contracts and
the checks within one session, so the result partly measures self-consistency.
The stronger test comes in v0.3, when `/amigos` authors a contract that this
validator did not anticipate.

### A contract about linting cannot quote the vocabulary it lints

The first real friction the protocol produced on itself.

STORY-003 specifies the vague-assertion rule. Its natural assertion would be:

```gherkin
And the finding names the word "correctly"
```

That is an assertion step containing `correctly`, so the rule fires on the
contract that specifies the rule. The contract was reworded:

```gherkin
And the finding names the offending word
```

The reworded clause is still independently judgeable, so nothing was lost here.
But the general shape is real: a contract that must discuss forbidden vocabulary
cannot state it directly while no suppression mechanism exists. This is the
first entry for the v0.7 failure corpus, and the first genuine argument for a
scoped suppression comment. Deliberately not acted on yet — README section 31
says to find out whether the rule is wrong before building the escape hatch, and
one occurrence is not yet evidence.

### A fixture that broke two rules

`ONECOUNTER-001` was first built by truncating a feature file mid-scenario,
which removed a `Then` as well as a counterexample, so it failed both
`counterexamples_present` and `assertions_are_determinable`. A fixture that
breaks two rules cannot prove which rule a failure came from. Rebuilt to break
exactly one; the corpus now holds that as an invariant in its own contract.

## Deviations from the plan

| Planned | Actual | Reason |
|---|---|---|
| `schemas/dor.schema.json` | plus `schemas/state.schema.json` | The split made `state.json` machine-readable too, so it earned a schema. |
| Six fixtures | Eleven | Added positive control `READY-001` and cases for placeholders, missing assertions, withheld state and unsupported Gherkin. |
| `amigos check` against fixtures | plus `--no-write` | Checking a fixture would otherwise write `dor.json` into the read-only corpus. |
| Plugin manifest declaring `skills/` and `agents/` | Neither declared | Those directories do not exist until v0.3; a manifest pointing at missing directories is a broken manifest. |

## Verification results

```text
python -m pytest -q                 139 passed
amigos status                       STORY-001 ready, STORY-002 ready, STORY-003 ready, exit 0
```

Every command in [action-plan.md](action-plan.md) was run and produced the exit
code and message recorded there. The eleven-story fixture corpus each failed for
its own single reason, and `amigos create STORY-999 && amigos check STORY-999`
exited 1.

## Follow-ups

- v0.2 must decide how the gate resolves the active story. Not decided here, to
  avoid designing an interface with no consumer.
- `then-before-when` stays a warning until enough real contracts exist to show
  it produces no false positives.
- Revisit lint suppression only if the STORY-003 friction recurs.
- `templates/` resolves from the checkout. If the package is ever published to
  PyPI independently of the plugin, the templates need to ship as package data.
