"""The Definition of Ready gate.

``dor.json`` is derived here and nowhere else. Nothing an agent writes can set
``ready`` to true: readiness is a function of the contract's content plus a
declared state that can only ever withhold it.

A structurally malformed story raises :class:`StructuralError` and no
``dor.json`` is written. Recording a readiness judgement about an input the
validator could not read would be worse than recording nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import __version__, jsonschema, markdown, story
from .config import Config
from .gherkin import ParseError, parse_file
from .lint import Finding, lint_feature

SCHEMA_VERSION = 1
DOR_FILENAME = "dor.json"

CHECK_NAMES = (
    "intent_defined",
    "scope_defined",
    "constraints_defined",
    "primary_scenario_present",
    "counterexamples_present",
    "assertions_are_determinable",
    "blocking_questions_resolved",
)

INTENT_SECTIONS = ("user", "problem", "desired outcome")
SCOPE_SECTIONS = ("in scope", "out of scope")
CONSTRAINT_SECTIONS = (
    "technical constraints", "dependencies", "invariants", "relevant components",
)
STRUCTURAL_LINT_RULES = ("untagged-scenario", "ambiguous-tag")

EXIT_READY = 0
EXIT_NOT_READY = 1
EXIT_STRUCTURAL = 2


class StructuralError(Exception):
    """The story cannot be evaluated at all, so no readiness record is produced."""


@dataclass
class Failure:
    check: str
    rule: str
    file: str
    message: str
    line: int | None = None
    scenario: str | None = None

    def as_dict(self) -> dict:
        return {
            "check": self.check, "rule": self.rule, "file": self.file,
            "line": self.line, "scenario": self.scenario, "message": self.message,
        }

    def format(self) -> str:
        where = self.file if self.line is None else f"{self.file}:{self.line}"
        return f"{where}: [{self.check}/{self.rule}] {self.message}"


@dataclass
class Result:
    story_id: str
    directory: Path
    checks: dict[str, bool]
    failures: list[Failure]
    blocking_questions: list[str]
    scenarios: dict[str, int]
    declared_state: str
    state: str
    ready: bool
    warnings: list[Finding]

    @property
    def exit_code(self) -> int:
        return EXIT_READY if self.ready else EXIT_NOT_READY

    def as_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "story_id": self.story_id,
            "state": self.state,
            "ready": self.ready,
            "declared_state": self.declared_state,
            "generated_at": story.now(),
            "generator": f"amigos {__version__}",
            "checks": {name: self.checks[name] for name in CHECK_NAMES},
            "failures": [f.as_dict() for f in self.failures],
            "blocking_questions": list(self.blocking_questions),
            "scenarios": dict(self.scenarios),
            "contract_hash": story.hash_inputs(self.directory),
        }


def evaluate(config: Config, story_id: str) -> Result:
    """Compute the Definition of Ready for one story. Writes nothing."""
    try:
        directory = story.story_dir(config, story_id)
    except story.StoryError as exc:
        raise StructuralError(str(exc)) from exc

    if not directory.is_dir():
        raise StructuralError(f"{directory}: story not found")

    missing = story.missing_inputs(directory)
    if missing:
        listed = ", ".join(missing)
        raise StructuralError(f"{directory}: missing contract file(s): {listed}")

    try:
        state = story.read_state(directory)
    except story.StoryError as exc:
        raise StructuralError(str(exc)) from exc

    feature_path = directory / "acceptance.feature"
    try:
        feature = parse_file(feature_path)
    except ParseError as exc:
        raise StructuralError(str(exc)) from exc

    findings = lint_feature(feature, config)
    structural = [f for f in findings if f.rule in STRUCTURAL_LINT_RULES]
    if structural:
        detail = "; ".join(f"{f.file}:{f.line}: {f.message}" for f in structural)
        raise StructuralError(
            f"scenario roles cannot be counted: {detail}"
        )

    failures: list[Failure] = []
    checks: dict[str, bool] = {}

    checks["intent_defined"] = _check_intent(directory, failures)
    checks["scope_defined"] = _check_scope(directory, failures)
    checks["constraints_defined"] = _check_constraints(directory, failures)

    roles = [scenario.roles[0] for scenario in feature.scenarios]
    counts = {
        "primary": roles.count("@primary"),
        "counterexample": roles.count("@counterexample"),
        "total": len(feature.scenarios),
    }
    checks["primary_scenario_present"] = _check_count(
        "primary_scenario_present", counts["primary"], config.min_primary,
        "@primary", str(feature_path), failures,
    )
    checks["counterexamples_present"] = _check_count(
        "counterexamples_present", counts["counterexample"], config.min_counterexamples,
        "@counterexample", str(feature_path), failures,
    )

    lint_failures = [f for f in findings if f.severity == "failure"]
    checks["assertions_are_determinable"] = not lint_failures
    for finding in lint_failures:
        failures.append(Failure(
            check="assertions_are_determinable", rule=finding.rule, file=finding.file,
            line=finding.line, scenario=finding.scenario, message=finding.message,
        ))

    blocking = _blocking_questions(directory, failures)
    checks["blocking_questions_resolved"] = not blocking

    declared = state.declared_state
    if declared in story.WITHHOLDING_STATES:
        effective, ready = declared, False
    elif all(checks.values()):
        effective, ready = "ready", True
    else:
        effective, ready = "blocked", False

    return Result(
        story_id=story_id, directory=directory, checks=checks, failures=failures,
        blocking_questions=blocking, scenarios=counts, declared_state=declared,
        state=effective, ready=ready,
        warnings=[f for f in findings if f.severity == "warning"],
    )


def write(result: Result) -> Path:
    """Write ``dor.json``. The validator is its only writer."""
    payload = result.as_dict()
    errors = jsonschema.validate(payload, jsonschema.load_schema("dor.schema.json"))
    if errors:
        raise StructuralError(
            "generated dor.json does not satisfy dor.schema.json: " + "; ".join(errors)
        )
    path = result.directory / DOR_FILENAME
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _check_intent(directory: Path, failures: list[Failure]) -> bool:
    path = directory / "intent.md"
    found = markdown.sections_of(path)
    ok = True
    for name in INTENT_SECTIONS:
        body = found.get(name)
        if body is None:
            failures.append(Failure(
                check="intent_defined", rule="missing-section", file=str(path),
                message=f"intent.md has no '## {name.title()}' section",
            ))
            ok = False
        elif not markdown.content_lines(body):
            failures.append(Failure(
                check="intent_defined", rule="empty-section", file=str(path),
                line=body[0][0] if body else None,
                message=f"'## {name.title()}' is empty or still holds scaffolding text",
            ))
            ok = False
    return ok


def _check_scope(directory: Path, failures: list[Failure]) -> bool:
    path = directory / "intent.md"
    found = markdown.sections_of(path)
    ok = True
    for name in SCOPE_SECTIONS:
        body = found.get(name)
        if body is None:
            failures.append(Failure(
                check="scope_defined", rule="missing-section", file=str(path),
                message=f"intent.md has no '## {name.title()}' section",
            ))
            ok = False
        elif not markdown.list_items(body):
            failures.append(Failure(
                check="scope_defined", rule="empty-section", file=str(path),
                line=body[0][0] if body else None,
                message=(
                    f"'## {name.title()}' lists nothing; state it explicitly, "
                    "'- None' included"
                ),
            ))
            ok = False
    return ok


def _check_constraints(directory: Path, failures: list[Failure]) -> bool:
    path = directory / "constraints.md"
    found = markdown.sections_of(path)
    populated = [name for name in CONSTRAINT_SECTIONS if markdown.list_items(found.get(name, []))]
    if populated:
        return True
    failures.append(Failure(
        check="constraints_defined", rule="empty-section", file=str(path),
        message=(
            "constraints.md populates none of: "
            + ", ".join(n.title() for n in CONSTRAINT_SECTIONS)
        ),
    ))
    return False


def _check_count(
    check: str, actual: int, minimum: int, tag: str, file: str, failures: list[Failure]
) -> bool:
    if actual >= minimum:
        return True
    failures.append(Failure(
        check=check, rule="scenario-count", file=file,
        message=f"found {actual} {tag} scenario(s); the contract requires at least {minimum}",
    ))
    return False


def _blocking_questions(directory: Path, failures: list[Failure]) -> list[str]:
    path = directory / "open-questions.md"
    found = markdown.sections_of(path)
    body = found.get("blocking")
    if body is None:
        failures.append(Failure(
            check="blocking_questions_resolved", rule="missing-section", file=str(path),
            message="open-questions.md has no '## Blocking' section",
        ))
        return ["open-questions.md has no '## Blocking' section"]
    items = markdown.list_items(body)
    for line, text in items:
        failures.append(Failure(
            check="blocking_questions_resolved", rule="open-blocker", file=str(path),
            line=line, message=f"unresolved blocking question: {text}",
        ))
    return [text for _, text in items]
