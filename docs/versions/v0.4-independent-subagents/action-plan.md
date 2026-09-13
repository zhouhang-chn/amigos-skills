# v0.4 Independent Subagents — Action Plan

Story covered: **STORY-005**.

Exit criterion, restated so it can be evaluated (the original could not be — see
`implementation-notes.md` for v0.3, which found this):

> A run records a findings record per role and a computed count of findings
> named by exactly one role. The multi-agent design survives only if that count
> is greater than zero on the milestone's own dogfooding run.

## Tasks

- [x] 1. `schemas/findings.schema.json` — the per-role record shape
- [x] 2. `src/amigos/findings.py` — load, validate, key, count, write the run record
- [x] 3. `amigos findings` in `src/amigos/cli.py`, plus `scripts/findings.py`
- [x] 4. `agents/product.md`, `agents/dev.md`, `agents/qa.md`
- [x] 5. `.claude/agents/` symlinks and `"agents": "./agents"` in the plugin manifest
- [x] 6. `skills/amigos/SKILL.md` — drafting, counting and reconciliation phases
- [x] 7. `tests/test_findings.py`, and additions to `tests/test_skill.py` and `tests/test_cli.py`
- [x] 8. README amendments: sections 8, 11, 12, 13, 19, 21, 22
- [x] 9. `docs/component-design/orchestration.md` — the split, the count, the run record
- [x] 10. Commit the implementation
- [!] 11. Dogfooding run: invoke `/amigos` as a registered skill to produce the v0.5 contract
      Blocked: all three drafting agents hit a session rate limit. The stop-the-run
      invariant fired correctly and nothing was written. See `implementation-notes.md`.
- [~] 12. `implementation-notes.md`, `milestones.md`, `docs/README.md`; commit; merge

Task 11 is the milestone, not a demonstration of it. Everything before it is
scaffolding for one measurement.

## Acceptance criteria

Taken from STORY-005's `acceptance.feature`, with where each is satisfied:

| Scenario | Satisfied by |
|---|---|
| The three roles draft without seeing each other | Separate agent types, prompts assembled before any agent runs; test that the skill never names a fork |
| A run records each role's findings separately | `.amigos/runs/<id>/<run>/findings/*.json`, each finding carrying its role |
| Two roles naming the same thing count as one finding | The `(target_section, risk_dimension)` key |
| A run in which the split adds nothing says so | `unique == 0`, `split_added_nothing: true`, and the verbatim sentence |
| A drafting agent that returns nothing stops the run | One atomic command over three records; exit 2 writes nothing |
| Reconciliation cannot grant readiness | Unchanged: `amigos check` is still the only writer of `dor.json` |
| A conflict between roles reaches the contract | `SKILL.md` reconciliation phase; no commentary file, enforced by the story directory holding only the five inputs |

## Verification

```bash
python -m pytest -q
amigos check STORY-005                    # exit 0
amigos status                             # every story ready, exit 0
amigos gate --staged                      # this slice passes its own gate

# the counting rules, against the fixture records
python scripts/findings.py READY-001 --stories-dir tests/fixtures/stories --no-write \
    --product tests/fixtures/findings/product.json \
    --dev     tests/fixtures/findings/dev.json \
    --qa      tests/fixtures/findings/qa.json        # 9 findings, 6 distinct, 4 unique

# ... the same call with --qa tests/fixtures/findings/empty.json  ->  exit 2, nothing written

# the milestone itself
/amigos STORY-006 "<the v0.5 ticket>"     # three subagents, a run record, a contract
cat .amigos/runs/STORY-006/*/summary.json # unique > 0, or the design does not survive
```

## Risks

| Risk | Mitigation |
|---|---|
| Vocabulary drift inflates the unique count and flatters the design | Identical suggested dimension list in all three agent files, asserted by a test |
| The key merges findings that are genuinely different | The key is the contract's literal wording; sources are kept in full in `summary.json`, so a wrong merge is visible rather than lost |
| One dogfooding run is one data point | Said plainly in the notes rather than dressed up. Runs accumulate; the question stays open until several exist |
| The orchestrator's reconciliation quietly favours one role | Every finding is in the run record with its role, so a contract that ignored a role is checkable after the fact |
| Three agents reading the whole repository is slow and expensive | Accepted. The milestone's entire question is whether that cost buys anything |
