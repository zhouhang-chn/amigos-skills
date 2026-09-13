"""Role findings records and the overlap count between them.

The Three Amigos split earns its cost only if the three roles find different
things. That claim is worth exactly as much as the method used to check it, so
the comparison happens here, in code, and not in a model's summary of its own
work.

Two findings are the same finding when they normalise to the same
``(target_section, risk_dimension)`` pair. ``target_file`` is deliberately not
part of the key: adding it would produce fewer collisions and inflate the count
of findings named by exactly one role, which is the number this design is judged
on. Where a choice biases a kill criterion, take the one that makes it harder to
pass.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, jsonschema, story
from .config import Config

ROLES = ("product", "dev", "qa")
RUNS_DIRNAME = "runs"
FINDINGS_DIRNAME = "findings"
SUMMARY_FILENAME = "summary.json"
RECORD_SCHEMA = "findings.schema.json"
SUMMARY_SCHEMA = "run-summary.schema.json"

# Printed verbatim when no role found anything the others missed. STORY-005 asks
# a run that gains nothing from the split to say so rather than quietly pass.
NOTHING_GAINED = "No role contributed a finding the others missed."

_WHITESPACE = re.compile(r"\s+")


class FindingsError(Exception):
    """A findings record is missing, malformed, empty or belongs elsewhere.

    Every one of these stops the run. A drafting agent that returned nothing
    usable is not a role with no opinion; it is a missing perspective, and a
    contract reconciled from the remaining two is not a Three Amigos contract.
    """


@dataclass(frozen=True)
class Finding:
    """One thing one role noticed, located and classified."""

    role: str
    target_file: str
    target_section: str
    risk_dimension: str
    statement: str

    @property
    def key(self) -> tuple[str, str]:
        return (normalise(self.target_section), normalise(self.risk_dimension))

    def as_dict(self) -> dict:
        return {
            "role": self.role,
            "target_file": self.target_file,
            "target_section": self.target_section,
            "risk_dimension": self.risk_dimension,
            "statement": self.statement,
        }


@dataclass(frozen=True)
class Record:
    """One role's findings, as returned by one drafting agent."""

    role: str
    story_id: str
    findings: tuple[Finding, ...]
    source: Path | None = None

    def as_dict(self) -> dict:
        return {
            "schema_version": 1,
            "story_id": self.story_id,
            "role": self.role,
            "findings": [f.as_dict() for f in self.findings],
        }


@dataclass(frozen=True)
class Key:
    """A distinct finding, and every role that named it."""

    target_section: str
    risk_dimension: str
    roles: tuple[str, ...]
    sources: tuple[Finding, ...]

    @property
    def shared(self) -> bool:
        return len(self.roles) > 1

    def as_dict(self) -> dict:
        return {
            "target_section": self.target_section,
            "risk_dimension": self.risk_dimension,
            "roles": list(self.roles),
            "shared": self.shared,
            "sources": [f.as_dict() for f in self.sources],
        }


@dataclass(frozen=True)
class Summary:
    """The counted overlap across all three roles."""

    story_id: str
    run_id: str
    generated_at: str
    findings_by_role: dict[str, int]
    unique_by_role: dict[str, int]
    keys: tuple[Key, ...]

    @property
    def total_findings(self) -> int:
        return sum(self.findings_by_role.values())

    @property
    def shared(self) -> int:
        return sum(1 for key in self.keys if key.shared)

    @property
    def unique(self) -> int:
        return sum(1 for key in self.keys if not key.shared)

    @property
    def split_added_nothing(self) -> bool:
        return self.unique == 0

    def as_dict(self) -> dict:
        return {
            "schema_version": 1,
            "story_id": self.story_id,
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "generator": f"amigos {__version__}",
            "findings_by_role": dict(self.findings_by_role),
            "total_findings": self.total_findings,
            "distinct_findings": len(self.keys),
            "shared": self.shared,
            "unique": self.unique,
            "unique_by_role": dict(self.unique_by_role),
            "split_added_nothing": self.split_added_nothing,
            "keys": [key.as_dict() for key in self.keys],
        }


def normalise(text: str) -> str:
    """Reduce a section or dimension to its comparable form.

    Heading markers go, because a role writing ``## In Scope`` and a role writing
    ``In Scope`` have named the same section.
    """
    return _WHITESPACE.sub(" ", text.lstrip("#").strip().lower())


def run_id() -> str:
    """A run identifier that is also a legal directory name everywhere."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def runs_dir(config: Config) -> Path:
    return config.stories_dir.parent / RUNS_DIRNAME


def load_record(path: Path, role: str, story_id: str) -> Record:
    """Read and validate one role's findings record.

    Raises ``FindingsError`` for anything that would let a run continue with a
    perspective missing or with another story's findings.
    """
    if role not in ROLES:
        raise FindingsError(f"unknown role {role!r}: expected one of {', '.join(ROLES)}")
    if not path.is_file():
        raise FindingsError(f"{path}: no findings record for the {role} role")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FindingsError(f"{path}: invalid JSON: {exc}") from exc

    errors = jsonschema.validate(payload, jsonschema.load_schema(RECORD_SCHEMA))
    if errors:
        raise FindingsError(f"{path}: does not satisfy {RECORD_SCHEMA}: " + "; ".join(errors))

    if payload["role"] != role:
        raise FindingsError(
            f"{path}: declares role {payload['role']!r} but was supplied as the {role} record"
        )
    if payload["story_id"] != story_id:
        raise FindingsError(
            f"{path}: belongs to story {payload['story_id']!r}, not {story_id!r}"
        )

    findings = []
    for index, item in enumerate(payload["findings"]):
        declared = item.get("role")
        if declared is not None and declared != role:
            raise FindingsError(
                f"{path}: finding {index} declares role {declared!r} inside the {role} record"
            )
        findings.append(Finding(
            role=role,
            target_file=item["target_file"],
            target_section=item["target_section"],
            risk_dimension=item["risk_dimension"],
            statement=item["statement"],
        ))
    return Record(role=role, story_id=story_id, findings=tuple(findings), source=path)


def load_records(story_id: str, paths: dict[str, Path]) -> tuple[Record, ...]:
    """Load all three records, or raise.

    All three at once is the point. There is no intermediate state in which two
    records have been accepted and a third is awaited, so there is no state from
    which a reconciliation could begin with two.
    """
    missing = [role for role in ROLES if role not in paths]
    if missing:
        raise FindingsError(f"no findings record supplied for: {', '.join(missing)}")
    return tuple(load_record(paths[role], role, story_id) for role in ROLES)


def summarise(story_id: str, records: tuple[Record, ...], identifier: str | None = None) -> Summary:
    """Count how much of what each role found, the others found too."""
    grouped: dict[tuple[str, str], list[Finding]] = {}
    for record in records:
        for finding in record.findings:
            grouped.setdefault(finding.key, []).append(finding)

    keys = []
    for (section, dimension), sources in grouped.items():
        roles = tuple(role for role in ROLES if any(f.role == role for f in sources))
        keys.append(Key(
            target_section=section,
            risk_dimension=dimension,
            roles=roles,
            sources=tuple(sources),
        ))
    keys.sort(key=lambda k: (not k.shared, k.target_section, k.risk_dimension))

    unique_by_role = {role: 0 for role in ROLES}
    for key in keys:
        if not key.shared:
            unique_by_role[key.roles[0]] += 1

    return Summary(
        story_id=story_id,
        run_id=identifier or run_id(),
        generated_at=story.now(),
        findings_by_role={record.role: len(record.findings) for record in records},
        unique_by_role=unique_by_role,
        keys=tuple(keys),
    )


def write(config: Config, summary: Summary, records: tuple[Record, ...]) -> Path:
    """Write the run record: the three records as filed, plus the summary.

    Runs accumulate rather than overwrite. STORY-005 asks for the count to be
    recorded for every run, and a count that survives only until the next run
    cannot answer whether roles disagree more or less over time.
    """
    directory = _reserve(runs_dir(config) / summary.story_id, summary.run_id)
    # The reserved name wins: a summary that claims a run id other than the one
    # on disk is a record nobody can find again.
    payload = replace(summary, run_id=directory.name).as_dict()
    errors = jsonschema.validate(payload, jsonschema.load_schema(SUMMARY_SCHEMA))
    if errors:
        directory.rmdir()
        raise FindingsError(
            f"generated summary does not satisfy {SUMMARY_SCHEMA}: " + "; ".join(errors)
        )

    (directory / FINDINGS_DIRNAME).mkdir(parents=True)
    for record in records:
        path = directory / FINDINGS_DIRNAME / f"{record.role}.json"
        path.write_text(json.dumps(record.as_dict(), indent=2) + "\n", encoding="utf-8")
    (directory / SUMMARY_FILENAME).write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return directory


def _reserve(parent: Path, identifier: str) -> Path:
    """Return a fresh run directory, disambiguating runs inside the same second."""
    candidate = parent / identifier
    suffix = 2
    while candidate.exists():
        candidate = parent / f"{identifier}-{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate
