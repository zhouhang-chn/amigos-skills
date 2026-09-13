# Development Workflow

## Versioning

- Goal versions: `v1.0`.
- Milestone versions: `v0.1`, `v0.2`, … while building toward a goal.
- Iteration versions: `v0.1.1` and so on, only inside a milestone that needs them.

Folder names are lowercase kebab-case and stay stable once created.

## Order of work

For each milestone, before implementation:

1. `gap-analysis.md` — current state, gaps, severity, non-goals, open questions.
2. `design.md` — architecture, data shapes, contracts, tests, alternatives.
3. `action-plan.md` — ordered tasks, statuses, verification commands, risks.

During implementation, fill `implementation-notes.md` with decisions,
deviations, bugs and verification results. If implementation materially changes
the design, update `design.md` rather than letting it drift.

Task statuses:

```text
- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Blocked
```

## Stories and milestones

A milestone's `action-plan.md` names the story IDs it covers. Every story has a
contract under `.amigos/stories/<id>/`, and no milestone is done while one of
its stories is not `ready`.

Which comes first depends on the phase. Through v0.1 the contracts are
hand-authored; from v0.3 they are produced by `/amigos`, and hand-authoring a
new contract becomes the exception that needs a reason.

## Working under the gate

From v0.2 this repository gates its own governed files. Start a slice by making
the story resolvable:

```bash
git switch -c story/STORY-123-short-description   # the branch names the story
amigos check STORY-123                            # must be ready before code
```

Contracts under `.amigos/` and docs under `docs/` are exempt, which is what lets
gap analysis, design and the contract itself be written before the story is
ready. Everything else — `src/`, `scripts/`, `schemas/`, `templates/`, `tests/`,
`integrations/`, and any directory added later — needs the story ready first.

If the gate refuses, it names the story it resolved and the check that failed.
Install the commit-time backstop once per checkout:

```bash
amigos hooks install
```

## Closeout

Before declaring a milestone done:

```bash
python -m pytest -q
amigos status              # every story ready, exit code 0
amigos gate --staged       # the slice's own changes pass the gate
```

Then record verification results in `implementation-notes.md`, update
`milestones.md`, promote durable decisions into `docs/component-design/` or the
root `README.md`, and commit the completed slice.

## The self-hosting invariant

From README section 31:

> No change to Amigos Skills should bypass a rule that the same version of
> Amigos Skills would impose on another project.

`tests/test_dogfooding.py` is that invariant written as tests: this repository's
own stories must pass the gate, and the committed `dor.json` must match a fresh
evaluation. If the framework becomes painful to use on itself, that is product
feedback, not a reason for a privileged path.
