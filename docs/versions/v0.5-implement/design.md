# v0.5 `/implement` — Design

Story: **STORY-006**.

## Shape of the slice

Two deliverables, matching the split every prior milestone used: a skill that
states the discipline, and deterministic code that makes one part of it
checkable.

```text
skills/implement/SKILL.md      the execution discipline, six phases
.claude/skills/implement       symlink, so the checkout runs the shipped file
amigos verify <STORY-ID>       re-derive readiness, diff the contract against
                               the hashes dor.json recorded
```

Nothing else. No new lifecycle state, no config key, no gate change.

## Why a verify command at all

`dor.json` already records a sha256 of each of the four contract input files
under `contract_hash`, written on every evaluation. Nothing has ever read it.

The milestone's exit criterion — "without redefining the requirement" — is
exactly the question that field answers, so the command is a comparison that was
already 90% built and never wired up.

```text
amigos verify STORY-006
  readiness   re-derived from the contract files     (never read from dor.json)
  contract    sha256 of each input file  vs  dor.json.contract_hash
  exit 0      ready, and every file matches
  exit 1      not ready, or at least one file differs
  exit 2      structurally unusable, or no baseline recorded
```

### What it deliberately does not catch

An agent that edits `acceptance.feature` **and then re-runs `amigos check`**
rewrites the baseline, and `verify` passes. That hole is real and is left open on
purpose: closing it means comparing against git rather than against a file in the
working tree, which is contract immutability, which is v0.6.

What `verify` catches is the case that actually occurs: a contract edited during
implementation and left behind. Recording the limit here so v0.6 does not have to
rediscover it.

## Readiness: recomputed, never read

`verify` calls `dor.evaluate()` and ignores `dor.json`'s `ready` field entirely.
It reads that file for one thing only: the recorded `contract_hash` baseline.

This is the resolution of the README-versus-gate conflict all three roles found.
`gate.py` already works this way, with the reason in its own source: a committed
verdict "may be stale, and it is writable by the agent being gated". A second
component trusting the file would be the weak link in a system whose whole claim
is that readiness cannot be self-declared.

README section 14 states the opposite and is the text that needs correcting.

## The skill's six phases

```text
0  Resolve      re-derive readiness; refuse to proceed unless ready
1  Load         the four contract files are the specification
2  Cover        map every scenario to the test or judgement that decides it
3  Red          a test for absent behaviour must fail before the source changes
4  Implement    the minimum those tests require, then run the suite
5  Report       coverage, changed files against scope, unsatisfied scenarios
```

Bounds that matter, each traceable to a scenario in the contract:

| Rule | Scenario it satisfies |
|---|---|
| Refuse unless readiness re-derives as ready | *A story that is not ready gets no implementation*; *A readiness verdict recorded in the story is not trusted on its own* |
| A new test fails before the source changes | *A test for absent behaviour fails before the source changes* |
| A `Then` no test can observe is named, with its judgement method, and excluded from the test-decided count | *A Then no test can observe is named rather than dropped* |
| An unsatisfied scenario stays in the suite, unskipped and failing | *An unsatisfied scenario is reported rather than made green* |
| Every changed governed file is listed with what it serves; the rest under scope expansion; the run continues | *A change no scenario requires is reported as scope expansion* |
| On conflict: report, declare `contract_change` last, stop without invoking `/amigos` | *A contract conflict stops the run instead of editing the contract* |
| Never edit settings, the pre-commit hook, or commit with it skipped | *The run takes no privileged path around the gate* |

### Why `contract_change` is declared last

Declaring it withholds readiness immediately, after which the gate refuses every
governed write — including committing the partial implementation already in the
tree. Declaring it as the final action, after the report is written, is the
ordering that loses the least. The question of whether partial work should be
saveable at all belongs to v0.6.

### Why the skill never invokes `/amigos`

A session that both discovers a conflict and authors the criterion replacing it
has no independent perspective between the two. The skill stops and hands to a
human, who runs `/amigos` themselves.

## The run record

`.amigos/runs/<STORY-ID>/<run-id>/` already exists as the place evidence about a
run lives — outside the story directory, because STORY-005 settled that no
commentary file goes inside it. An implementation run writes its report there,
beside the drafting evidence for the same story.

The skill writes this as Markdown; no schema is added. The run record is read by
people, not by agents, and inventing a schema for it now would be a protocol
change this story put out of scope.

## Data shapes

`verify` adds no new persisted artifact. Its JSON form, for a caller that wants
one:

```json
{
  "schema_version": 1,
  "story_id": "STORY-006",
  "ready": true,
  "state": "ready",
  "baseline": "dor.json",
  "contract": {
    "intent.md": "match",
    "constraints.md": "match",
    "acceptance.feature": "differs",
    "open-questions.md": "match"
  },
  "changed": ["acceptance.feature"],
  "verified": false
}
```

`verified` is `ready and not changed`. It is computed, never stored.

## Tests

| File | What it holds |
|---|---|
| `tests/test_verify.py` | The command: match, differ, missing baseline, not-ready, structurally unusable, and that a stale `ready: true` in `dor.json` never produces exit 0. |
| `tests/test_skill_implement.py` | The skill file against the code, the `test_skill.py` pattern: every command it names exists in the parser, every state it names is declarable, and each bound above appears in the text. |
| `tests/test_cli.py` | `verify` is registered and its exit codes are the documented ones. |

The scenarios about agent behaviour — red-before-green, scope reporting, no
privileged path — are held by `test_skill_implement.py` as instructions present
in the prompt, not as executed behaviour. That is the honest limit of testing a
prompt, and is the same limit `test_skill.py` already documents for `/amigos`.

## Alternatives rejected

- **Ship the skill alone.** Smallest slice, but "the implementer must not rewrite
  the criteria" stays prose with nothing checking it, and the exit criterion
  keeps having no artifact.
- **Add a test-command config key.** Would make "run tests" resolvable
  downstream, but it is a protocol schema change and belongs with the other
  protocol work rather than riding along here.
- **Compare against git HEAD instead of `dor.json`.** Strictly better detection,
  and it is v0.6's job. Doing it here would implement contract immutability under
  a milestone that declared it out of scope.
- **A new lifecycle state, `implementing`.** Would need a schema change and a
  validator rule about whether it withholds readiness. `draft` already means
  "not under an amigos run", which is accurate during implementation.
