"""The repository gate: refuse a governed change without a ready story.

One decision function, consulted by every adapter. The Claude Code hook and the
git pre-commit hook collect changed paths and translate an exit code; neither
holds a rule of its own, because two implementations of one rule drift.

Readiness is recomputed from the contract files on every call. A committed
``dor.json`` describes the contract as it was when the record was written, and
it is writable by the very agent being gated, so it is a record and never an
authority.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import dor, story
from .config import Config

ACTIVE_FILE = "ACTIVE"
ENV_VAR = "AMIGOS_STORY"

PERMITTED = 0
REFUSED = 1
UNAVAILABLE = 2

SOURCE_ENV = "environment"
SOURCE_POINTER = "pointer file"
SOURCE_BRANCH = "branch name"

RESOLUTION_ORDER = (
    f"the {ENV_VAR} environment variable",
    f"the .amigos/{ACTIVE_FILE} pointer file",
    "a story id in the branch name",
)


class GateUnavailable(Exception):
    """The gate could not determine what it was being asked about."""


@dataclass
class Decision:
    permitted: bool
    reason: str
    governed: list[str] = field(default_factory=list)
    exempt: list[str] = field(default_factory=list)
    story_id: str | None = None
    story_source: str | None = None
    state: str | None = None

    @property
    def exit_code(self) -> int:
        return PERMITTED if self.permitted else REFUSED

    def as_dict(self) -> dict:
        return {
            "permitted": self.permitted,
            "reason": self.reason,
            "governed": self.governed,
            "exempt": self.exempt,
            "story_id": self.story_id,
            "story_source": self.story_source,
            "state": self.state,
        }


# --------------------------------------------------------------------------
# Path classification
# --------------------------------------------------------------------------

def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a path glob. ``*`` stops at a separator, ``**`` crosses them."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if pattern[i:i + 3] == "**/":
                out.append(r"(?:.*/)?")
                i += 3
                continue
            if pattern[i:i + 2] == "**":
                out.append(r".*")
                i += 2
                continue
            out.append(r"[^/]*")
            i += 1
            continue
        if char == "?":
            out.append(r"[^/]")
        else:
            out.append(re.escape(char))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def is_exempt(path: str, patterns: tuple[str, ...]) -> bool:
    normalised = path.replace(os.sep, "/")
    while normalised.startswith("./"):
        normalised = normalised[2:]
    return any(_glob_to_regex(p).match(normalised) for p in patterns)


def classify(paths: list[str], config: Config) -> tuple[list[str], list[str]]:
    """Split paths into (governed, exempt). Governed is the default."""
    governed, exempt = [], []
    for path in paths:
        (exempt if is_exempt(path, config.gate_exempt) else governed).append(path)
    return governed, exempt


# --------------------------------------------------------------------------
# Active story resolution
# --------------------------------------------------------------------------

def known_story_ids(config: Config) -> list[str]:
    if not config.stories_dir.is_dir():
        return []
    return sorted(d.name for d in config.stories_dir.iterdir() if d.is_dir())


def current_branch(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True, check=False,
        )
    except (OSError, ValueError):
        return None
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def stories_named_in(text: str, candidates: list[str]) -> list[str]:
    """Story IDs appearing in ``text``, bounded so STORY-001 misses STORY-0011."""
    found = []
    for candidate in candidates:
        pattern = re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(candidate) + r"(?![A-Za-z0-9])"
        )
        if pattern.search(text):
            found.append(candidate)
    return found


def resolve_story(config: Config, override: str | None = None) -> tuple[str | None, str | None, str | None]:
    """Return (story_id, source, problem). Exactly one of story_id or problem is set."""
    if override:
        return override, "explicit argument", None

    from_env = os.environ.get(ENV_VAR, "").strip()
    if from_env:
        return from_env, SOURCE_ENV, None

    pointer = config.root / ".amigos" / ACTIVE_FILE
    if pointer.is_file():
        for line in pointer.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return line.strip(), SOURCE_POINTER, None

    branch = current_branch(config.root)
    if branch:
        matches = stories_named_in(branch, known_story_ids(config))
        if len(matches) == 1:
            return matches[0], SOURCE_BRANCH, None
        if len(matches) > 1:
            return None, None, (
                f"the branch name {branch!r} names more than one story "
                f"({', '.join(matches)}); the gate does not choose between them"
            )

    places = "; ".join(RESOLUTION_ORDER)
    return None, None, f"no active story could be resolved. Looked in: {places}"


# --------------------------------------------------------------------------
# The decision
# --------------------------------------------------------------------------

def decide(config: Config, paths: list[str], override: str | None = None) -> Decision:
    governed, exempt = classify(paths, config)

    if not governed:
        return Decision(
            permitted=True,
            reason="no governed path was changed",
            governed=governed, exempt=exempt,
        )

    story_id, source, problem = resolve_story(config, override)
    if story_id is None:
        return Decision(
            permitted=False,
            reason=f"{len(governed)} governed path(s) changed but {problem}",
            governed=governed, exempt=exempt,
        )

    try:
        result = dor.evaluate(config, story_id)
    except (dor.StructuralError, story.StoryError) as exc:
        return Decision(
            permitted=False,
            reason=f"story {story_id} ({source}) cannot be evaluated: {exc}",
            governed=governed, exempt=exempt,
            story_id=story_id, story_source=source,
        )

    if result.ready:
        return Decision(
            permitted=True,
            reason=f"story {story_id} ({source}) is ready",
            governed=governed, exempt=exempt,
            story_id=story_id, story_source=source, state=result.state,
        )

    failed = [name for name in dor.CHECK_NAMES if not result.checks[name]]
    if failed:
        detail = f"failed check(s): {', '.join(failed)}"
    else:
        detail = f"state.json declares {result.declared_state}"
    return Decision(
        permitted=False,
        reason=f"story {story_id} ({source}) is {result.state}; {detail}",
        governed=governed, exempt=exempt,
        story_id=story_id, story_source=source, state=result.state,
    )


# --------------------------------------------------------------------------
# Collecting changed paths
# --------------------------------------------------------------------------

def _git(root: Path, *args: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        raise GateUnavailable(f"git is unavailable: {exc}") from exc
    if result.returncode != 0:
        raise GateUnavailable(
            f"git {' '.join(args)} failed: {result.stderr.strip() or 'unknown error'}"
        )
    return [line for line in result.stdout.splitlines() if line.strip()]


def staged_paths(root: Path) -> list[str]:
    return _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRT")


def working_tree_paths(root: Path) -> list[str]:
    tracked = _git(root, "diff", "--name-only", "--diff-filter=ACMRT")
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))
