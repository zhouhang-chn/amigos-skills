# v1.0 Self-Hosting — Design

## Target

```text
Amigos Skills develops Amigos Skills, with no privileged path around its own
protocol.
```

## Layering

```text
 contract protocol   .amigos/         v0.1  format, schemas, templates
 deterministic core  src/amigos/      v0.1  parse, lint, judge
 repository gate     hooks, CI        v0.2  refuse source changes without ready
 orchestration       skills/          v0.3  /amigos produces contracts
 role independence   agents/          v0.4  Product, Development, QA
 execution           skills/          v0.5  /implement consumes contracts
 strong enforcement  hooks            v0.6  contract immutability, state integrity
 flywheel            evals/           v0.7  failures become regressions
```

Each layer is only worth building once the one beneath it is trustworthy. A gate
built on a validator that can be argued with is not a gate.

## Decisions held across milestones

- **Readiness is derived, never declared.** The split between agent-owned
  `state.json` and validator-owned `dor.json` is the mechanism. Every later
  milestone reads `dor.json` and never trusts `state.json` for readiness.
- **Structural defects produce no verdict.** Exit code 2 stays distinct from
  exit code 1 so the gate can tell "needs work" from "unreadable".
- **`contract_hash` starts being recorded in v0.1** so v0.6 has a baseline to
  diff against without a format change.
- **The protocol stays platform-independent.** Claude Code specifics live in
  `.claude-plugin/` and `skills/`; Codex specifics will live in their own
  mirror. Neither leaks into `.amigos/`.

## Alternatives rejected

- *A single `dor.json` written by the agent and corrected by the validator.*
  Cheaper, and it preserves the appearance of the README's original file list,
  but it leaves an agent writing into the file that decides readiness. The split
  costs one file and removes the question.
- *Heuristic detection of counterexamples from negation vocabulary.* No
  authoring burden, but it makes the gate's most important count depend on
  wording, which is exactly the model-ish judgement the gate exists to replace.
