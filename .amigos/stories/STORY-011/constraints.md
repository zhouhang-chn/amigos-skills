# Constraints

## Technical Constraints

- **What is detectable is bounded by what the file records.** `set_state()` takes
  a state and a free-text note and writes them; there is no key, no signature and
  no writer identity. A forged entry naming a declarable state and a plausible
  timestamp is byte-identical to one the command would have produced. The
  detectable class is therefore: a `declared_state` that disagrees with the last
  `history` entry, an `updated_at` that disagrees with that entry's `at`, a
  `history` that is not an append-only extension of the committed one, and a
  payload that cannot be parsed. A well-formed forgery is outside that class and
  nothing here puts it inside.
- **`state.json` is supposed to change, so equality with the committed copy
  cannot carry this rule.** STORY-009's model — the file must not move during
  implementation — does not transfer. A story mid-drafting has uncommitted
  transitions by design. The transferable rule is append-only: the committed
  `history` must be a prefix of the working tree's `history`, compared as parsed
  entries rather than as bytes.
- **The refusal is a gate decision, never a readiness verdict.** Readiness
  derivation is untouched: `dor.evaluate()` keeps honouring a withholding
  `declared_state` however it was written. Routing this through readiness would
  invert it — a story reported as tampered would evaluate as not ready, and
  `gate.frozen_contracts()` freezes only a story that demonstrably evaluates
  ready, so the report would *release* the contract it exists to protect.
- **One rule, one implementation, consulted wherever it is reported.** The gate's
  refusal and the `amigos state` report answer the same question and must not
  hold two definitions of it. `verify._governed_in()` already reuses
  `gate.classify()` rather than restating it; this follows that arrangement.
- **The exit vocabularies are fixed and already assigned.** `gate`: 0 permitted /
  1 refused / 2 the gate could not run. `state` today exits 0 or 2 and has no
  meaning for 1, so the report takes 0 consistent / 1 inconsistent / 2 could not
  read. No new subcommand is added, and `--set` becomes optional rather than
  changing meaning.
- **The repair path must not deadlock.** A `state.json` that cannot be parsed
  cannot be repaired by `amigos state`, because `set_state()` parses the file
  before writing it. A write to a story's own `state.json` is therefore permitted
  while that story's record is inconsistent. This mirrors STORY-010's scaffolding
  permit, and without it a single damaged file makes a repository unworkable.
- **Nothing new is written into `state.json`.** `schemas/state.schema.json` is
  `additionalProperties: false`, requires `schema_version`, `story_id`,
  `declared_state` and `updated_at`, and closes history items to `state`, `at`
  and `note`. A sequence number, a chain hash or a writer marker is a schema
  change every committed `state.json` and every fixture must then satisfy. This
  story adds no field.
- **`classify()` keeps its path-only, time-independent semantics.** STORY-009's
  `verify._governed_in()` runs it over historical commits. As in STORY-010, the
  new question is asked alongside classification, never through it.
- **`.amigos/**` stays exempt.** Removing the exemption deadlocks contract
  authoring. The refusal is a second question about a resolved story, not a
  widening of what "governed" means.
- **Git is partial evidence.** `git show HEAD:<path>` needs `state.json` tracked
  and committed. A rebase, an amend or `git commit --no-verify` rewrites the
  evidence, and enforcement outside the session is milestone task 3. Anything
  landing here is in-session only, and that limit is recorded rather than implied
  away.
- **An unanswered question never reads as clean, and never reads as tampered.**
  No repository, no work tree, or a `state.json` never committed is "could not
  tell". It does not by itself produce a refusal, and it is not reported as
  consistent.
- **The mechanism lands in code, not in a SKILL.md.** README section 18: the
  system must not depend on an agent remembering the process. The skills may
  describe the rule; a rule that exists only there is what this milestone closes.
- Runtime stays stdlib-only on Python 3.11+, git stays a subprocess, and
  `.amigos/` names no git ref, CI host or execution environment.

## Dependencies

- `story.read_state()`, `story.set_state()`, `story.State.history`,
  `story.DECLARABLE_STATES` and `story.WITHHOLDING_STATES` — the whole of what
  `state.json` means today.
- `gate.decide()`, `gate.resolve_story()`, `gate.contract_file()`,
  `gate.frozen_contracts()`, `gate._ready_before_change()` and the `Decision`
  record, whose keys keep their meaning and gain new ones additively.
- `gate._git_bytes()` and `verify.work_tree_root()` for reading the committed
  copy. The gate must not adopt `verify._git`, which raises `NoBaseline` and
  exits 2 where the gate needs its own answer.
- `dor.evaluate()` for the derived `blocked` state and the failed check names the
  refusal quotes.
- `cli._state()` and `cli._gate()` for the two reports, and `build_parser()` for
  making `--set` optional.
- `schemas/state.schema.json` and `templates/state.json`, which define a
  well-formed record and the one every new story starts from.
- **The test corpus contains one record the rule rejects.**
  `tests/fixtures/stories/RUNNING-001/state.json` declares `amigos_running` while
  its only history entry is `draft`. Every other fixture and all ten of this
  repository's stories satisfy the rule as written. RUNNING-001 is reached by
  `tests/test_dor.py:107` and `tests/test_cli.py:26`, neither of which runs the
  gate, so the rule as designed does not break them; the fixture is named here so
  that making it coherent is planned rather than discovered.
- `tests/test_dor.py::test_contract_change_also_withholds_readiness` hand-writes
  `declared_state` into READY-001 with no history entry and asserts the
  declaration withholds readiness. That assertion stays true: this story changes
  the gate, not readiness derivation.
- `tests/conftest.py` provides `scratch_repo`, `git_repo`, `on_branch` and
  `committed_repo`. The git-backed shapes here build on `committed_repo`.
- `amigos state <id> --set contract_change` remains the documented route out of a
  frozen contract, named in `cli._gate()`, in `gate._frozen_reason()` and in both
  SKILL.md files.
- **This story's own branch must resolve to this story.** On
  `story/STORY-010-gate-refuses-contract-edit` the gate resolves STORY-010, which
  is ready, so governed writes for STORY-011 would be permitted by another
  story's readiness — the privileged path this milestone removes. A branch,
  `.amigos/ACTIVE` or `AMIGOS_STORY` naming STORY-011 comes before any governed
  write.

## Invariants

- **Readiness stays derived, never declared.** Nothing here lets a file grant
  readiness, and no verdict is persisted for the judged agent to rewrite.
- **Detection never becomes an unlock.** A story reported as inconsistent ends up
  no more editable than it was before the report. This is the invariant the whole
  design turns on, because `_ready_before_change()` fails open.
- **STORY-010's fail-open rule is a shipped contract.** Its `constraints.md` and
  its scenario *A story whose contract cannot be evaluated stays editable* both
  state it. Changing it is a contract change on STORY-010, not a side effect of
  this one.
- **`state.json` stays outside `story.HASHED_FILES` and outside
  `dor.json.contract_hash`.** That exclusion keeps `contract_change` declarable
  while a story is ready, keeps every committed `contract_hash` valid, and keeps
  STORY-009's baseline derived from four paths.
- **History is appended to, never replaced.** This story reads that evidence; it
  gives nothing a way to rewrite it.
- **The protocol does not deadlock.** `create` → `amigos_running` → `draft`, and
  `contract_change` → stop, stay performable and committable, and a record the
  gate rejects stays repairable.
- **No exemption exists for Amigos Skills that an adopting project would not
  get.** `tests/test_dogfooding.py` keeps passing over this repository's stories.
- **The claim is difficulty, not impossibility.** The limits — a well-formed
  forgery, a rebase, `--no-verify`, `Bash` writes — are written down.
- Closeout still passes: the suite, `amigos status` exit 0, `amigos verify` for
  this story, and `amigos gate --staged` permitting this slice's own changes.

## Relevant Components

- `src/amigos/gate.py` — `decide()`, `resolve_story()`, `contract_file()`,
  `frozen_contracts()`, `_ready_before_change()`, `_git_bytes()`, `Decision`
- `src/amigos/story.py` — `read_state()`, `set_state()`, `State`, `INPUT_FILES`
- `src/amigos/dor.py` — `evaluate()`, the withholding branch, `StructuralError`
- `src/amigos/cli.py` — `_state()`, `_gate()`, `build_parser()`
- `src/amigos/verify.py` — `work_tree_root()` and the git helpers
- `schemas/state.schema.json`, `templates/state.json`
- `tests/conftest.py`, `tests/test_state.py`, `tests/test_dor.py`,
  `tests/test_cli.py`, `tests/test_gate.py`, `tests/test_gate_contract_freeze.py`,
  `tests/test_dogfooding.py`, `tests/fixtures/stories/RUNNING-001/state.json`
- `integrations/claude-code/gate_hook.py`, `src/amigos/hooks.py` — the adapters,
  which hold no rules
- `docs/component-design/gate.md`, `docs/component-design/contract-protocol.md`
- `docs/versions/v0.6-strong-enforcement/{gap-analysis,design,action-plan,implementation-notes}.md`
