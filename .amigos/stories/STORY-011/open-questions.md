# Open Questions

## Blocking

None.

## Non-blocking

- Should `.amigos/config.json` and `.amigos/ACTIVE` be guarded? Both change the
  gate's verdict without touching a contract file — the first by rewriting the
  exempt list, the second by naming which story is resolved — and both are
  writable by the agent being gated. Neither is named by gap 8. They are siblings
  of gap 5 and STORY-010 recorded the config half already.
- Should `schemas/state.schema.json` be enforced by shipped code? Today only
  `tests/test_dogfooding.py` validates against it, over an allowlist of six story
  ids, so this repository holds itself to a check it does not ship to the projects
  it asks to adopt the protocol. `read_state()` ignores unknown keys, a missing
  `schema_version`, and a `story_id` that disagrees with the directory name.
- Should a transition require a reason? `set_state()` treats `note` as optional,
  so `amigos state <id> --set contract_change` with no `--note` records a
  reopening carrying no explanation. That is an unexplained change through the
  sanctioned route, which is a different hole from an unrecorded one.
- Does a rewrite committed with `git commit --no-verify` stay invisible? The
  append-only comparison is against HEAD, so once a laundering commit lands the
  working tree and HEAD agree again. The commit itself is refused at the
  pre-commit adapter, which is why this is not blocking, but `--no-verify` is
  gap 4 and is still open.
- Should `tests/fixtures/stories/RUNNING-001/state.json` be made coherent? It
  declares `amigos_running` while its only history entry is `draft`, which the
  rule rejects. No test reaching it runs the gate, so nothing breaks today, but a
  fixture the shipped rule would refuse is a trap for the next gate test written
  over it.
- Should the refusal distinguish an inconsistent record from an unparseable one?
  Both refuse, and the contract requires only that `state.json` is named. A
  reviewer repairing the file may want to know which of the two they are looking
  at.
