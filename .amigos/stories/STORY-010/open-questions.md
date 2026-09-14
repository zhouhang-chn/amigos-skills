# Open Questions

## Blocking

None.

## Non-blocking

- Should `.amigos/config.json` be protected while a story is ready? It carries
  `gate.exempt` and `stories_dir`, it is itself exempt, and an agent working
  under a ready story can repoint or widen it and switch off the refusal this
  story adds. Gap 5 covers the same hole in `.claude/settings.json` and names
  this file nowhere. It is a sibling of gap 5 rather than part of this story.
- Is corrupting `state.json` a silent unlock? The rule fails open, so a story
  whose state cannot be read is not ready and its contract stays editable. QA
  named this; Development's answer is that a broken contract must stay
  repairable, and that a hand-written `contract_change` already unlocks it just
  as cheaply. Both are gap 8, task 5 of this milestone.
- Can partial work survive a contract conflict? Declaring `contract_change` to
  reopen a contract withholds readiness immediately, after which the gate refuses
  every governed write for that story, including committing implementation
  already in the tree. That is gap 7, carried unanswered from v0.5, and shipping
  this refusal makes it load-bearing rather than merely known.
- Should the `PreToolUse` adapter have tests of its own?
  `integrations/claude-code/gate_hook.py` has none, so its deny payload, its
  message text and its behaviour on error are exercised by hand alone. This story
  judges the rule through the command and lets the adapter inherit it, which is
  what `gate.md` already asks of adapters.
- Does adding `D` to `gate.staged_paths()` change decisions beyond this story? A
  staged deletion of a governed source path would begin to require a ready story,
  which is what fail-closed already implies and what the collector omits today.
  The effect is intended here and is worth watching once CI exists.
