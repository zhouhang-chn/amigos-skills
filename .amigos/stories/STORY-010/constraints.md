# Constraints

## Technical Constraints

- The refusal is **one rule with one implementation**, consulted by every
  adapter. `docs/component-design/gate.md` states this as the gate's organising
  rule: adapters collect paths and translate an exit code, and none holds a rule,
  because two implementations of one rule drift invisibly.
- `gate.classify()` keeps its current path-only, time-independent semantics.
  `verify._governed_in()` calls it over historical commits to derive STORY-009's
  baseline, so a classification that consulted present-day readiness would judge
  past commits by today's state and move the baseline STORY-009 was built to fix.
  The refusal is therefore a second question asked alongside classification, not
  a change to what "governed" means.
- Whether a path is a contract file is a property of its **location under
  `config.stories_dir`**, not of its filename. `stories_dir` is configurable and
  `--stories-dir` can point outside the git work tree, so the mapping from path
  to story id is derived from configuration, never from the literal prefix
  `.amigos/stories/`.
- Paths reach the decision with different origins per adapter, and the rule names
  the origin it assumes rather than leaving it to the caller: the Claude Code
  hook passes a path relative to `config.root`; `gate.staged_paths()` returns
  paths relative to the git work-tree root, which need not be `config.root`;
  `--changed-file` passes whatever the caller typed.
- Readiness for this decision is derived from the contract **before the change**:
  the working tree at edit time, `HEAD` at commit time. It is recomputed on every
  call and never read from a committed `dor.json`.
- The declared state is read live from `state.json`, which is not a contract file
  and stays writable. Any declaration that withholds readiness reopens the
  contract; the rule keys on derived readiness, not on which state was declared.
- This rule fails **open**, the opposite of the gate's fail-closed default, and
  so is written down rather than inferred: a path is refused only when the story
  that owns it demonstrably evaluates ready. A story that cannot be evaluated —
  malformed Gherkin, a missing file, an unknown id — is not ready and must stay
  editable, or a broken contract can never be repaired.
- The fail-open path is implemented inside the decision, not left to the adapter.
  `integrations/claude-code/gate_hook.py` wraps `gate.decide()` in no
  `try`/`except`, so a new exception escaping it changes what the hook does on
  error rather than producing a deny.
- Nothing outside `config.stories_dir` can be refused by this rule. The rule
  takes effect inside the session that writes it, so a too-broad rule can lock
  the implementing session out of the files it needs in order to fix it.
- The exit-code vocabulary is fixed: 0 permitted, 1 refused, 2 the gate could not
  run. A refusal caused by a contract edit is still a refusal; "I could not tell"
  stays distinct from "you may not".
- `Decision` carries one `story_id` and one `state`, and a refusal about a
  contract path may concern a story other than the resolved active one. Existing
  `--json` keys keep their meaning; anything new is additive.
- The refusal names the file and the legitimate route. `cli._gate()` currently
  ends every refusal with `Make the story ready, then retry: amigos check <id>`
  or `Set an active story with one of...`; both are the wrong instruction here,
  because the change is refused precisely because the story **is** ready.
- Runtime stays stdlib-only on Python 3.11+, and git stays a subprocess.

## Dependencies

- `dor.evaluate()` for readiness, `story.HASHED_FILES` for which files constitute
  a contract, `config.stories_dir` and `story.STORY_ID_RE` for mapping a path to
  a story id, `gate.classify()` for what is governed.
- STORY-009's git helpers in `verify.py` for reading a contract at `HEAD`. The
  commit-time question is *was this contract ready before the change*, which is
  the same history the baseline is derived from.
- `amigos state <id> --set contract_change` is the only legitimate exit from a
  ready contract, and it withholds readiness immediately — after which the gate
  refuses every governed write for that story, including committing work already
  in the tree. That is gap 7, sequenced outside this story. Shipping the refusal
  makes that gap load-bearing rather than merely known.
- `.amigos/**` stays in `gate.exempt`. Removing it gates the work that makes a
  story ready and deadlocks the protocol, which is why the exemption exists.
- The mechanism's reach is bounded by gaps this story does not close: `Bash`
  writes are not seen by the `PreToolUse` matcher (gap 6), `git commit
  --no-verify` skips the pre-commit adapter (gap 4), `.claude/settings.json` is
  editable under a ready story (gap 5), and a hand-edited `state.json` defeats
  the readiness input directly (gap 8).
- The fixture corpus already holds both a ready story (`READY-001`) and stories
  that raise on evaluation (`BADGHERKIN-001`, `MISSING-001`, `SELFPROMO-001`).
  `tests/conftest.py` provides `scratch_repo`, `git_repo` and `committed_repo`.

## Invariants

- **The protocol does not deadlock.** From any ready contract a permitted
  sequence of steps reaches a changed one, and a contract just made ready by
  `/amigos` stays committable. `/amigos` Phase 7 returns a story to `draft`, at
  which point it computes ready, so the commit that lands the contract stages
  four contract files of a now-ready story.
- `state.json` and `dor.json` stay writable while a story is ready. Neither is in
  `story.HASHED_FILES`, and that exclusion is load-bearing: it keeps
  `contract_change` reachable and keeps the validator the only writer of
  `dor.json`.
- Readiness stays derived, never declared.
- A change touching only exempt paths, and no ready story's contract, stays
  permitted with no story resolvable — `docs/**`, `*.md`, `.amigos/config.json`,
  `.amigos/runs/**` and the story directory's derived files included.
- The gate keeps answering when the corpus is unreadable. An unevaluable story is
  not a refusal, and an unknown story id under `stories_dir` is not a refusal.
- The rule does not claim to make a contract edit impossible. README section 18's
  standard is that skipping the contract is *harder* than following it; the
  documented route stays available and visible.
- No exemption is added for Amigos Skills that a downstream project adopting the
  same version would not get. `tests/test_dogfooding.py` keeps passing.
- Closeout still passes: the suite, `amigos status` exit 0, `amigos verify` for
  this story, and `amigos gate --staged` permitted for this slice's own changes.

## Relevant Components

- `src/amigos/gate.py` — `decide()`, `classify()`, `staged_paths()`, `Decision`
- `src/amigos/config.py` — `stories_dir`, `gate_exempt`
- `src/amigos/dor.py`, `src/amigos/story.py`
- `src/amigos/verify.py` — the other caller of `gate.classify()`, and the git
  helpers the commit-time question reuses
- `src/amigos/cli.py` — `_gate()`'s refusal output
- `integrations/claude-code/gate_hook.py`, `src/amigos/hooks.py`
- `tests/test_gate.py`, `tests/test_dogfooding.py`, `tests/conftest.py`
- `docs/component-design/gate.md`, `docs/component-design/execution.md`
- `skills/implement/SKILL.md`, `skills/amigos/SKILL.md` — both currently state
  that this rule holds *without* enforcement
