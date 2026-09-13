"""Story workspace: paths, scaffolding, and the agent-owned lifecycle file."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Config

INPUT_FILES = (
    "intent.md",
    "constraints.md",
    "acceptance.feature",
    "open-questions.md",
    "state.json",
)
HASHED_FILES = ("intent.md", "constraints.md", "acceptance.feature", "open-questions.md")
DERIVED_FILE = "dor.json"

# States an agent is permitted to declare. `ready` and `blocked` are absent by
# design: they are derived by the validator, never declared.
DECLARABLE_STATES = ("draft", "amigos_running", "contract_change")
# Declaring either of these withholds readiness no matter what the checks say.
WITHHOLDING_STATES = ("amigos_running", "contract_change")

STORY_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*$")

# The templates ship beside the package inside the plugin checkout. A target
# repository may also carry its own copy at <root>/templates.
_PACKAGE_TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


class StoryError(Exception):
    """A story workspace is missing or structurally unusable."""


@dataclass(frozen=True)
class State:
    """The agent-owned lifecycle record read from ``state.json``."""

    declared_state: str
    updated_at: str
    history: tuple[dict, ...] = ()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_story_id(story_id: str) -> None:
    if not STORY_ID_RE.match(story_id or ""):
        raise StoryError(
            f"invalid story id {story_id!r}: expected a leading letter followed by "
            "letters, digits, dot, underscore or hyphen"
        )


def story_dir(config: Config, story_id: str) -> Path:
    validate_story_id(story_id)
    return config.story_dir(story_id)


def missing_inputs(directory: Path) -> list[str]:
    """Return the contract input files that are absent, in canonical order."""
    return [name for name in INPUT_FILES if not (directory / name).is_file()]


def read_state(directory: Path) -> State:
    """Read and validate ``state.json``.

    Raises ``StoryError`` when an agent has tried to declare a state it does not
    own. Catching that attempt is the point of splitting this file from dor.json.
    """
    path = directory / "state.json"
    if not path.is_file():
        raise StoryError(f"{path}: missing")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StoryError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise StoryError(f"{path}: expected a JSON object")

    declared = data.get("declared_state")
    if declared is None:
        raise StoryError(f"{path}: missing required key 'declared_state'")
    if declared in ("ready", "blocked"):
        raise StoryError(
            f"{path}: declared_state {declared!r} is not declarable. Readiness is "
            "derived by the validator and written to dor.json; state.json may "
            f"declare only {', '.join(DECLARABLE_STATES)}."
        )
    if declared not in DECLARABLE_STATES:
        raise StoryError(
            f"{path}: unknown declared_state {declared!r}; "
            f"expected one of {', '.join(DECLARABLE_STATES)}"
        )

    history = data.get("history") or []
    if not isinstance(history, list):
        raise StoryError(f"{path}: 'history' must be an array")

    return State(
        declared_state=declared,
        updated_at=str(data.get("updated_at", "")),
        history=tuple(h for h in history if isinstance(h, dict)),
    )


def hash_inputs(directory: Path) -> dict[str, str]:
    """SHA-256 of each contract input file, the baseline for later immutability checks."""
    digests: dict[str, str] = {}
    for name in HASHED_FILES:
        path = directory / name
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            digests[name] = f"sha256:{digest}"
    return digests


def _resolve_templates(config: Config, override: Path | None) -> Path:
    """First existing templates directory, in order of specificity."""
    candidates = [override, _PACKAGE_TEMPLATES, config.root / "templates"]
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    searched = ", ".join(str(c) for c in candidates if c is not None)
    raise StoryError(f"templates directory not found; searched: {searched}")


def set_state(directory: Path, declared: str, note: str | None = None) -> State:
    """Record a lifecycle transition in ``state.json``.

    Refuses ``ready`` and ``blocked`` here exactly as :func:`read_state` refuses
    them, so the rule holds whichever end of the file something approaches from.
    History is appended to, never replaced: a contract's lifecycle is evidence.
    """
    path = directory / "state.json"
    if not path.is_file():
        raise StoryError(f"{path}: missing")
    if declared in ("ready", "blocked"):
        raise StoryError(
            f"{declared!r} is not declarable. Readiness is derived by the validator "
            f"and written to dor.json; state.json may declare only "
            f"{', '.join(DECLARABLE_STATES)}."
        )
    if declared not in DECLARABLE_STATES:
        raise StoryError(
            f"unknown state {declared!r}; expected one of {', '.join(DECLARABLE_STATES)}"
        )

    data = json.loads(path.read_text(encoding="utf-8"))
    timestamp = now()
    entry: dict = {"state": declared, "at": timestamp}
    if note:
        entry["note"] = note
    history = data.get("history")
    data["history"] = ([*history] if isinstance(history, list) else []) + [entry]
    data["declared_state"] = declared
    data["updated_at"] = timestamp
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return read_state(directory)


def create(config: Config, story_id: str, templates_dir: Path | None = None) -> Path:
    """Scaffold a story workspace from the templates.

    Never overwrites: an existing directory is an error, so a scaffold can not
    silently discard a contract someone was working on.
    """
    validate_story_id(story_id)
    directory = config.story_dir(story_id)
    if directory.exists():
        raise StoryError(f"{directory}: already exists; refusing to overwrite an existing story")

    source = _resolve_templates(config, templates_dir)

    timestamp = now()
    directory.mkdir(parents=True)
    for name in INPUT_FILES:
        template = source / name
        if not template.is_file():
            raise StoryError(f"{template}: template not found")
        body = template.read_text(encoding="utf-8")
        body = body.replace("__STORY_ID__", story_id).replace("__TIMESTAMP__", timestamp)
        (directory / name).write_text(body, encoding="utf-8")
    return directory
