# Open Questions

## Blocking

None.

## Non-blocking

- Should the gate refuse a contract edit while a story is ready, rather than
  only detecting it afterwards? Development's drafting showed edit-time and
  commit-time refusal are different rules, and that a commit-time refusal scoped
  to the story directory would refuse this project's own closeout commits. It
  needs its own story in v0.6.
- What happens when a story has more than one implementation branch, or when
  branches are rebased so the first governed commit is rewritten? The baseline
  is derived from history reachable from the current commit, so a rebase moves
  it. Deliberate history rewriting is a louder act than re-running a command,
  which is why it is not treated as the same class of problem.
- Should `dor.json.contract_hash` eventually be retired now that it is no longer
  the authority? Retiring it is a schema change across every committed story and
  buys little while it still answers the question in a checkout without git.
- Should `amigos verify` accept an explicit revision, for a caller such as CI
  that knows the range it wants to judge? No caller needs it until CI exists.
