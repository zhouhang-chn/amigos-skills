# Constraints

## Technical Constraints
- Readiness is recomputed from the contract files, never read from a committed
  `dor.json`. `src/amigos/gate.py` already treats a committed verdict as a record
  and never an authority, because it may be stale and is writable by the agent
  being gated. README section 14 says the opposite and is the outdated text;
  whatever `/implement` consults must reach the verdict the gate would reach.
- The runtime stays stdlib-only on Python 3.11 or newer. `pyproject.toml` keeps
  `dependencies = []`; pytest stays an optional dev extra.
- The skill layer adds no second definition of an existing rule. Readiness
  belongs to `amigos check`, the write-time refusal belongs to `amigos gate`. A
  skill restating either in prose creates two implementations that drift.
- Anything the skill instructs that code does not enforce is held to the code by
  a test, the pattern `tests/test_skill.py` and `tests/test_agents.py` establish:
  a named command exists in the parser, a named state is declarable, a named
  check exists in `dor.CHECK_NAMES`.
- `skills/implement/SKILL.md`, its `.claude/skills/` symlink, the new command's
  source, and any new test file are **governed** paths. The exempt set is
  `.amigos/**`, `docs/**`, top-level `*.md`, `LICENSE`, `.gitignore`, and `*`
  does not cross a separator, so nothing under `skills/`, `src/`, `.claude/` or
  `tests/` is exempt. STORY-006 must be ready *and* resolvable before any of them
  can be written.
- `.claude-plugin/plugin.json` already declares `"skills": "./skills"`, so a
  second skill needs no manifest change. The checkout discovers the shipped file
  through a symlink rather than a second copy, as `skills/amigos` does.
- `state.json` accepts only `draft`, `amigos_running` and `contract_change`;
  `schemas/state.schema.json` pins that enum with `additionalProperties: false`.
  Recording an implementation run in the lifecycle is a schema change.
- Declaring `contract_change` withholds readiness immediately, after which the
  gate and the pre-commit hook refuse every governed write, including committing
  the partial implementation already in the working tree. The skill therefore
  declares it as its last action, after reporting, and leaves the working tree
  for the human.
- A skill edited during a session serves its previously registered text until
  something re-registers it, recorded in
  `docs/versions/v0.4-independent-subagents/implementation-notes.md`. The session
  that writes `skills/implement/SKILL.md` is not the session that can invoke it.
- Writes made through `Bash` are not gated; `docs/component-design/gate.md`
  records this as a tolerated hole. `/implement` is the first skill that needs
  `Bash`, to run tests, so it is the first consumer for which that hole is
  load-bearing.
- README section 14's "business code" is read as the gate's "governed files".
  The two vocabularies are not reconciled anywhere else, and the gate's is the
  one with an implementation.

## Dependencies
- v0.4 must close first. `milestones.md` lists v0.5 as depending on it, and its
  exit criterion is a computed count that changes whether the subagent design
  survives at all.
- `amigos check` (v0.1) supplies the readiness verdict. `amigos gate` and the two
  hook adapters (v0.2) supply the write-time refusal. `/implement` consumes both.
- `dor.json.contract_hash` and `story.hash_inputs()` already exist and record the
  SHA-256 of each contract input file. Nothing currently compares against them;
  the new command is that comparison.
- No eval harness exists: no `evals/` directory, no grader runner, no
  `amigos export-evals`. README places eval export at Phase 7 / STORY-008.
- No configured test command exists. `.amigos/config.json` carries `stories_dir`,
  `lint`, `dor` and `gate`, and `config.py` reads no other key. "Run tests"
  resolves to `python -m pytest -q` here by `docs/development-workflow.md`, and
  to nothing at all in a downstream repository.
- The gate resolves an active story from `AMIGOS_STORY`, `.amigos/ACTIVE`, or a
  story id in the branch name. This checkout is on a detached HEAD, where nothing
  resolves and the first governed write is refused.
- A ready story that `/implement` can consume. STORY-001 to STORY-005 and
  STORY-007 are implemented; STORY-006 builds the skill itself, so the
  demonstrating story is v0.6's first and does not exist yet.

## Invariants
- The four contract input files are byte-identical before and after an
  implementation run, judged against `dor.json.contract_hash`.
- Readiness stays derived. The skill never writes `dor.json` and never declares
  `ready` or `blocked`; `story.read_state` and `story.set_state` refuse both.
- A contract problem found during implementation surfaces as `contract_change`
  and a stop, never as an edit to the contract that makes a test pass.
- A story that is not ready, does not exist, or is structurally unusable stops
  the run before any governed file is written. `dor.evaluate` raises
  `StructuralError` and writes no `dor.json` for the last case.
- The run takes no privileged path around a refusal: it does not edit
  `.claude/settings.json`, uninstall the pre-commit hook, or commit with the hook
  skipped. README section 31 forbids a privileged path for this repository.
- Every existing verification keeps passing at closeout: `python -m pytest -q`,
  `amigos status` exit 0, `amigos gate --staged` permitted.
- `.amigos/` stays platform-independent. Claude Code specifics live in `skills/`,
  `agents/`, `.claude/` and `.claude-plugin/` and must not leak into the protocol.

## Relevant Components
- `skills/implement/SKILL.md` and its `.claude/skills/` symlink
- `skills/amigos/SKILL.md` — the shape a skill file takes here, and the handoff
  at its Phase 7
- `src/amigos/dor.py`, `src/amigos/gate.py` — the readiness verdict and the
  write-time refusal
- `src/amigos/story.py`, `schemas/state.schema.json` — the closed lifecycle
  vocabulary, `INPUT_FILES` and `hash_inputs`
- `src/amigos/cli.py` — the command surface a skill is allowed to name
- `integrations/claude-code/gate_hook.py`, `integrations/git/` — the two adapters
  an implementation run writes through
- `tests/test_skill.py`, `tests/test_dogfooding.py` — where a skill is held to the
  code, and where the story list is enumerated as a literal tuple that omits
  STORY-006
- `.claude-plugin/plugin.json`, `.amigos/config.json`
- `README.md` section 14 and the section 0 status table; `docs/roadmaps.md`,
  `docs/versions/v1.0-self-hosting/milestones.md`, `docs/versions/v0.5-*/`
