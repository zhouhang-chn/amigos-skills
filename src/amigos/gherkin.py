"""A deliberately small, deterministic Gherkin parser.

Only the subset the contract format uses is supported. Anything outside that
subset raises :class:`ParseError` rather than being skipped, because a construct
the validator silently ignores is a construct through which an unjudgeable
assertion can enter a ready contract.

Supported: a single ``Feature``, an optional ``Background``, ``Scenario`` and
``Scenario Outline`` with ``Examples``, tag lines, ``Given/When/Then/And/But``
steps, ``#`` comments, triple-quoted doc strings and pipe-delimited data tables.

Every element records the 1-based line it was read from.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")
CONJUNCTIONS = ("And", "But")

_STEP_RE = re.compile(r"^(Given|When|Then|And|But)\b[ \t]*(.*)$")
_TAG_RE = re.compile(r"^@[^\s@]+$")
_DOCSTRING_RE = re.compile(r'^("""|\'\'\')')


class ParseError(Exception):
    """The feature file uses a construct outside the supported subset."""

    def __init__(self, message: str, path: Path | str, line: int) -> None:
        super().__init__(f"{path}:{line}: {message}")
        self.path = str(path)
        self.line = line
        self.message = message


@dataclass(frozen=True)
class Step:
    keyword: str
    """The keyword as written, including And and But."""
    effective_keyword: str
    """And and But resolved to the Given, When or Then they continue."""
    text: str
    line: int

    @property
    def is_assertion(self) -> bool:
        """True for a Then, and for the And or But steps that continue one."""
        return self.effective_keyword == "Then"


@dataclass
class Scenario:
    name: str
    line: int
    keyword: str = "Scenario"
    tags: tuple[str, ...] = ()
    steps: list[Step] = field(default_factory=list)
    examples_line: int | None = None

    @property
    def roles(self) -> tuple[str, ...]:
        """The contract-role tags carried by this scenario."""
        return tuple(t for t in self.tags if t in ("@primary", "@counterexample"))


@dataclass
class Feature:
    name: str
    line: int
    path: str
    tags: tuple[str, ...] = ()
    background: Scenario | None = None
    scenarios: list[Scenario] = field(default_factory=list)


def parse_file(path: Path | str) -> Feature:
    path = Path(path)
    return parse(path.read_text(encoding="utf-8"), path)


def parse(text: str, path: Path | str = "<string>") -> Feature:
    lines = text.splitlines()
    feature: Feature | None = None
    pending_tags: list[str] = []
    pending_tag_line: int | None = None
    current: Scenario | None = None
    in_examples = False
    index = 0

    def fail(message: str, line_no: int) -> ParseError:
        return ParseError(message, path, line_no)

    while index < len(lines):
        raw = lines[index]
        line_no = index + 1
        index += 1
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            continue

        # Tag line: applies to the next Feature or Scenario.
        if stripped.startswith("@"):
            tags = stripped.split()
            for tag in tags:
                if not _TAG_RE.match(tag):
                    raise fail(f"malformed tag {tag!r}", line_no)
            if pending_tags:
                raise fail("two tag lines in a row; put all tags on one line", line_no)
            pending_tags = tags
            pending_tag_line = line_no
            continue

        keyword, _, remainder = stripped.partition(":")
        keyword = keyword.strip()
        title = remainder.strip()
        is_block = bool(_) and keyword in (
            "Feature", "Background", "Scenario", "Scenario Outline",
            "Example", "Examples", "Rule",
        )

        if is_block:
            if keyword == "Rule":
                raise fail("'Rule:' is outside the supported Gherkin subset", line_no)

            if keyword == "Feature":
                if feature is not None:
                    raise fail("a contract holds exactly one Feature", line_no)
                feature = Feature(
                    name=title, line=line_no, path=str(path), tags=tuple(pending_tags)
                )
                pending_tags, pending_tag_line = [], None
                current, in_examples = None, False
                continue

            if feature is None:
                raise fail(f"'{keyword}:' appears before the Feature", line_no)

            if keyword == "Background":
                if feature.background is not None:
                    raise fail("a contract holds at most one Background", line_no)
                if pending_tags:
                    raise fail("a Background cannot carry tags", pending_tag_line or line_no)
                current = Scenario(name=title, line=line_no, keyword="Background")
                feature.background = current
                in_examples = False
                continue

            if keyword in ("Scenario", "Scenario Outline", "Example"):
                normalised = "Scenario Outline" if keyword == "Scenario Outline" else "Scenario"
                current = Scenario(
                    name=title,
                    line=line_no,
                    keyword=normalised,
                    tags=tuple(pending_tags),
                )
                feature.scenarios.append(current)
                pending_tags, pending_tag_line = [], None
                in_examples = False
                continue

            if keyword == "Examples":
                if current is None or current.keyword != "Scenario Outline":
                    raise fail("'Examples:' without a preceding Scenario Outline", line_no)
                current.examples_line = line_no
                in_examples = True
                continue

        # Step line.
        match = _STEP_RE.match(stripped)
        if match:
            if current is None:
                raise fail("step appears outside a Scenario or Background", line_no)
            if in_examples:
                raise fail("step appears inside an Examples block", line_no)
            step_keyword, step_text = match.group(1), match.group(2).strip()
            effective = step_keyword
            if step_keyword in CONJUNCTIONS:
                previous = current.steps[-1] if current.steps else None
                if previous is None:
                    raise fail(
                        f"'{step_keyword}' has no preceding Given, When or Then to continue",
                        line_no,
                    )
                effective = previous.effective_keyword
            current.steps.append(
                Step(keyword=step_keyword, effective_keyword=effective,
                     text=step_text, line=line_no)
            )
            continue

        # Data table row, attached to the step or Examples block above it.
        if stripped.startswith("|"):
            if current is None:
                raise fail("data table appears outside a Scenario or Background", line_no)
            continue

        # Doc string, consumed whole so its content is never read as Gherkin.
        fence = _DOCSTRING_RE.match(stripped)
        if fence:
            if current is None or not current.steps:
                raise fail("doc string does not follow a step", line_no)
            delimiter = fence.group(1)
            closed = False
            while index < len(lines):
                if lines[index].strip().startswith(delimiter):
                    index += 1
                    closed = True
                    break
                index += 1
            if not closed:
                raise fail("doc string is never closed", line_no)
            continue

        raise fail(f"unrecognised line {stripped!r}", line_no)

    if feature is None:
        raise ParseError("no Feature found", path, 1)
    if pending_tags:
        raise ParseError("tag line is not followed by a Scenario", path, pending_tag_line or 1)
    for scenario in feature.scenarios:
        if scenario.keyword == "Scenario Outline" and scenario.examples_line is None:
            raise ParseError(
                f"Scenario Outline {scenario.name!r} has no Examples block",
                path, scenario.line,
            )
    return feature
