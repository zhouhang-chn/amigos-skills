"""Acceptance criteria lint rules.

One implementation, two consumers: the standalone ``lint_acceptance`` command
and the ``assertions_are_determinable`` Definition of Ready check.

The rules judge whether a clause *can* be evaluated, never whether the behaviour
it describes is worth testing. That second question stays with the Three Amigos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .gherkin import Feature, Scenario, parse_file

FAILURE = "failure"
WARNING = "warning"

ROLE_TAGS = ("@primary", "@counterexample")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    scenario: str | None = None
    word: str | None = None

    def format(self) -> str:
        where = f"{self.file}:{self.line}"
        return f"{where}: {self.severity}: [{self.rule}] {self.message}"


def _word_pattern(entry: str) -> re.Pattern[str]:
    """Whole-word, case-insensitive matcher; runs of whitespace match loosely."""
    parts = [re.escape(part) for part in entry.split()]
    return re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.IGNORECASE)


def _patterns(config: Config) -> list[tuple[str, re.Pattern[str]]]:
    return [(entry, _word_pattern(entry)) for entry in config.vague_words]


def lint_feature(feature: Feature, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    patterns = _patterns(config)
    path = feature.path

    blocks: list[Scenario] = []
    if feature.background is not None:
        blocks.append(feature.background)
    blocks.extend(feature.scenarios)

    for block in blocks:
        is_scenario = block.keyword != "Background"
        label = block.name or block.keyword

        for step in block.steps:
            if not step.text:
                findings.append(Finding(
                    rule="empty-step", severity=FAILURE, file=path, line=step.line,
                    scenario=label,
                    message=f"'{step.keyword}' has no text; a step with no text asserts nothing",
                ))
                continue
            if not step.is_assertion:
                continue
            for entry, pattern in patterns:
                if pattern.search(step.text):
                    findings.append(Finding(
                        rule="vague-assertion", severity=FAILURE, file=path, line=step.line,
                        scenario=label, word=entry,
                        message=(
                            f"assertion uses {entry!r}, which two reviewers can read "
                            "differently; state the observable outcome instead"
                        ),
                    ))

        if not is_scenario:
            continue

        roles = block.roles
        if not roles:
            findings.append(Finding(
                rule="untagged-scenario", severity=FAILURE, file=path, line=block.line,
                scenario=label,
                message=(
                    f"scenario declares no contract role; tag it {ROLE_TAGS[0]} or {ROLE_TAGS[1]}"
                ),
            ))
        elif len(roles) > 1:
            findings.append(Finding(
                rule="ambiguous-tag", severity=FAILURE, file=path, line=block.line,
                scenario=label,
                message=(
                    f"scenario carries {' and '.join(roles)}; a scenario has exactly one role"
                ),
            ))

        if not any(step.is_assertion for step in block.steps):
            findings.append(Finding(
                rule="missing-then", severity=FAILURE, file=path, line=block.line,
                scenario=label,
                message="scenario has no Then step, so it asserts nothing",
            ))
        else:
            first_then = next(s.line for s in block.steps if s.is_assertion)
            whens = [s.line for s in block.steps if s.effective_keyword == "When"]
            if whens and first_then < min(whens):
                findings.append(Finding(
                    rule="then-before-when", severity=WARNING, file=path, line=first_then,
                    scenario=label,
                    message="assertion precedes the action it judges",
                ))

    findings.sort(key=lambda f: (f.line, f.rule))
    return findings


def lint_file(path: Path | str, config: Config) -> list[Finding]:
    """Parse and lint one feature file. Propagates ParseError."""
    return lint_feature(parse_file(path), config)


def failures(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == FAILURE]
