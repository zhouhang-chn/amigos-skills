# v1.0 Self-Hosting — Action Plan

Milestone-level tracking. Task-level plans live in each milestone folder.

| Status | Milestone | Stories |
|---|---|---|
| [x] | v0.1 contract format and deterministic validator | STORY-001, STORY-002, STORY-003 |
| [x] | v0.2 repository gate | STORY-007 |
| [ ] | v0.3 `/amigos` MVP | STORY-004 |
| [ ] | v0.4 three independent subagents | STORY-005 |
| [ ] | v0.5 `/implement` | STORY-006 |
| [ ] | v0.6 strong self-hosting enforcement | to be defined |
| [ ] | v0.7 dogfooding failure corpus and evals | STORY-008 |

Story numbering follows README section 26. v0.2 takes STORY-007 ahead of
STORY-004 because README section 32 places the repository gate before agent
orchestration.

## Verification

```bash
python -m pytest -q
amigos status
```

The goal is met when every milestone above is complete and a source change made
without a ready story fails mechanically rather than by reminder.

## Risks

| Risk | Mitigation |
|---|---|
| The gate becomes painful enough to invite an escape hatch | Treat the pain as product feedback first; fix the contract model, skill or mechanism before adding a bypass. |
| Three subagents produce duplicated prose | v0.4 exit criterion is evidence of *different* classes of finding, not just three outputs. |
| The protocol drifts toward Claude Code | Keep `.amigos/` free of platform specifics; build the Codex mirror before claiming portability. |
