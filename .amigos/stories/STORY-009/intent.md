# Intent

## User
The maintainer or reviewer of any repository that has adopted amigos-skills, who
has to trust one answer: was the requirement redefined while it was being
implemented? Today that answer is produced by a comparison the implementing
agent can reset, so it carries no more weight than the agent's own word.

Immediately that user is this project. Every remaining v0.6 protection assumes
the contract a story is judged against is stable.

## Problem
`amigos verify` asks the right question against the wrong baseline. It hashes
the four contract files in the working tree and compares them to
`dor.json.contract_hash` — but `amigos check` rewrites that field on every
invocation, and `.amigos/**` is exempt from the gate, so nothing refuses the
edit in the first place.

The laundering path is not an exotic attack. It is the cheapest repair available
when a test derived from a `Then` clause fails: edit the criterion, re-run
`amigos check`, and `verify` reports the contract intact. `/implement`'s own
Phase 0 runs `amigos check`, so the baseline is rewritten on the happy path
without anyone intending it.

The result is worse than no check. A green `verify` is today indistinguishable
between "the contract never moved" and "the contract moved and the record of
where it started was overwritten".

## Desired Outcome
The contract a story is judged against is the contract as committed to git
history, at a revision fixed by the point implementation began rather than by
the run being judged.

That revision is the parent of the earliest commit that changed a governed path
for this story. A contract edit committed during implementation is therefore
newer than the baseline and cannot become it, which is the property that makes
this different from comparing against the latest commit.

`amigos verify` gives one of three distinguishable answers: the contract matches
the baseline; it differs, and the differing files are named; or no baseline can
be established, which is reported as a question that cannot be answered rather
than as a pass.

## Why Now
v0.5 shipped `verify` with this hole documented in `src/amigos/verify.py` and in
`docs/component-design/execution.md`, and deferred it here by name. It is phase
6's first protection and gap 1 of the v0.6 gap analysis. Every later phase-6
protection assumes a baseline that cannot be moved from inside the session.

## In Scope
- Moving the baseline `amigos verify` judges against from
  `dor.json.contract_hash` in the working tree onto the contract as committed.
- Deriving the baseline revision from history: the parent of the earliest commit
  changing a governed path for this story, and the current commit when no such
  commit exists.
- Naming the baseline revision in the command's output, so a reader can check
  the comparison rather than trust it.
- Three distinguishable outcomes, including an unanswerable one that never reads
  as verified.
- Comparing contract files the way git compares them, so a repository with
  content filters configured does not report differences that are not there.
- Keeping every story already in this repository verifiable under the new
  baseline.
- Recording what the new baseline still does not catch, in the durable docs,
  where v0.5 recorded the hole this story closes.

## Out of Scope
- Mechanically refusing a contract edit while a story is ready. Development's
  drafting showed edit-time and commit-time refusal are different rules, and
  that a naive commit-time refusal makes a freshly authored contract
  uncommittable. It needs its own story in v0.6.
- Retiring `dor.json.contract_hash`. It is `required` in `dor.schema.json` under
  `additionalProperties: false`, present in every committed `dor.json`, and
  asserted by two tests. It stays; the git baseline becomes the authority.
- The other phase 6 protections: CI outside the session, gating `Bash` writes,
  `git commit --no-verify`, a session disabling its own hook, blocked stories,
  and detecting a hand-edited `state.json`.
- The contract change workflow — diffs and explicit reapproval — which is phase 8.
- Any change to the seven Definition of Ready checks, the lint vocabulary, the
  declared-state enum, or the gate's decision.
- Making `amigos check` stop writing `dor.json` on every invocation.
- Renumbering STORY-008, which README section 26 reserves for eval export and
  which STORY-006's ready contract references.
- Requiring, as an acceptance criterion, that this story is built by
  `/implement`. That obligation is recorded in v0.5's docs and in
  `milestones.md`; nothing observable distinguishes a run record written by the
  skill from one written by hand.
- Autonomous commits, branch creation and pull requests.

## Success
A reviewer can tell from git history alone whether the contract moved after
implementation began, and no command the implementing agent is told to run
changes that answer. An agent that edits `acceptance.feature` and then re-runs
`amigos check` is reported as having changed the contract, by name and by file.
Where the question cannot be answered, the run says so instead of saying
verified.
