# Open Questions

## Blocking

None.

## Non-blocking

- Whether the Claude Code hook should also gate Bash tool calls that write
  files. Deferred until the Edit and Write path has been used enough to show
  whether the hole matters in practice.
- Whether a repository should be able to add governed patterns as well as
  exempt ones. No repository has asked, and the fail-closed default already
  governs everything.
