# Intent

## User
Anyone deciding whether a story may move into implementation: a human reviewer,
a coding agent about to start work, and later a repository gate or CI job.

## Problem
Readiness is currently a judgement call. If the model that drafted the contract
also decides the contract is ready, the gate measures the model's confidence
rather than the contract's quality. A contract can be declared ready while it
still has placeholder sections, one lone scenario, or an open blocking question.

## Desired Outcome
A command reads a story's contract files and computes readiness from their
content alone. It writes a derived record of that computation, and its exit code
is usable directly by a script. No model input participates in the decision, and
nothing an agent writes can promote a story to ready.

## Why Now
This is the first trustworthy primitive in the system. The repository gate, the
/amigos skill and the /implement skill all need a readiness answer they can
believe. Until this exists, every later layer rests on self-assessment.

## In Scope
- Computing the seven Definition of Ready checks from the contract input files.
- Deriving the effective story state from the checks and the declared state.
- Generating dor.json as the sole writer of that file.
- Recording a content hash of each input file as a baseline for later contract
  immutability enforcement.
- Distinguishing a not-ready story from a structurally malformed one through
  separate exit codes.
- Parsing the Gherkin subset the contract format uses, with line numbers.

## Out of Scope
- The wording rules for acceptance criteria themselves. This story consumes the
  linter as a library; STORY-003 owns its rules.
- Blocking any file modification. The gate is a later milestone.
- Repairing or rewriting a contract that fails.
- Explaining how to fix a failing check beyond naming the file and line.

## Success
A reviewer can run one command and get an answer they do not have to second
guess, and a story with a hidden defect cannot reach ready by being argued for.
