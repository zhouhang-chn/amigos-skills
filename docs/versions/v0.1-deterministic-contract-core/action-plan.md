# v0.1 Deterministic Contract Core — Action Plan

Stories covered: **STORY-001**, **STORY-002**, **STORY-003**.

## Tasks

| Status | Task | Acceptance |
|---|---|---|
| [x] | Project scaffolding: `pyproject.toml`, `LICENSE`, plugin manifest, `.gitignore` | `amigos --version` resolves |
| [x] | Templates, schemas, `.amigos/config.json` | Every JSON file parses; templates carry visible placeholders |
| [x] | Hand-author STORY-001, STORY-002, STORY-003 | Five input files each, written before any validator exists |
| [x] | `config.py`, `story.py`, `scripts/create_story.py` | Scaffolding produces five files and refuses to overwrite |
| [x] | `gherkin.py` | Line-accurate parse; unsupported constructs raise |
| [x] | `lint.py`, `scripts/lint_acceptance.py` | Six rules; vocabulary bounded to assertion steps |
| [x] | `markdown.py`, `dor.py`, `scripts/check_dor.py` | Seven checks; `dor.json` generated and schema-valid |
| [x] | `cli.py` | `init`, `create`, `check`, `lint`, `status` |
| [x] | Fixture corpus and test suite | Each fixture fails for exactly one reason |
| [x] | Run the validator against the hand-authored stories | All three ready |
| [x] | Docs and README amendments | Sections 4, 5, 16, 20, 21, 22 match the implementation |

## Verification

```bash
python -m pytest -q

python scripts/check_dor.py STORY-001    # exit 0
python scripts/check_dor.py STORY-002    # exit 0
python scripts/check_dor.py STORY-003    # exit 0
amigos check STORY-002 --json            # ready true

S=tests/fixtures/stories
amigos check --stories-dir $S --no-write READY-001        # exit 0
amigos check --stories-dir $S --no-write VAGUE-001        # exit 1, cites the line and the word
amigos check --stories-dir $S --no-write BLOCKED-001      # exit 1, blocking question listed
amigos check --stories-dir $S --no-write ONECOUNTER-001   # exit 1, counterexamples_present false
amigos check --stories-dir $S --no-write PLACEHOLDER-001  # exit 1, intent_defined false
amigos check --stories-dir $S --no-write NOTHEN-001       # exit 1, missing-then
amigos check --stories-dir $S --no-write RUNNING-001      # exit 1, state withheld
amigos check --stories-dir $S --no-write UNTAGGED-001     # exit 2, roles cannot be counted
amigos check --stories-dir $S --no-write SELFPROMO-001    # exit 2, state.json declared ready
amigos check --stories-dir $S --no-write MISSING-001      # exit 2, missing constraints.md
amigos check --stories-dir $S --no-write BADGHERKIN-001   # exit 2, unsupported construct

amigos create STORY-999 && amigos check STORY-999          # exit 1
```

The last two lines are the milestone's proof: the validator refuses to be talked
into readiness, and an empty scaffold is not a ready contract.

## Risks

| Risk | Mitigation |
|---|---|
| The Gherkin subset is too narrow for real contracts | Unsupported constructs raise a named error, so the gap is visible rather than silent. |
| The vocabulary produces false positives | Scanning is limited to assertion steps and bounded to whole words; the list is repository-tunable. |
| A hand-edited `dor.json` goes unnoticed | `tests/test_dogfooding.py` compares every committed record against a fresh evaluation. |
