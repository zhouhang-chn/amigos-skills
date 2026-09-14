"""The repository gate: refuse a governed change without a ready story.

One decision function, consulted by every adapter. The Claude Code hook and the
git pre-commit hook collect changed paths and translate an exit code; neither
holds a rule of its own, because two implementations of one rule drift.

Readiness is recomputed from the contract files on every call. A committed
``dor.json`` describes the contract as it was when the record was written, and
it is writable by the very agent being gated, so it is a record and never an
authority.

STORY-010 added a second question, asked alongside the first. ``.amigos/**`` is
exempt because gating the story directory would deadlock the protocol: a story
can only become ready by editing a story. That single exemption also left a
finished contract unprotected, so a contract input file of a story that is
**ready** is refused even though its path is exempt.

Readiness for that question is derived from the contract *before* the change:
the working tree when an edit is attempted, ``HEAD`` when a staged set is
committed. At commit time the tree already holds the edited contract, and
deleting a counterexample is itself an edit that leaves a story unready — so a
tree-derived rule would permit the most damaging edits and refuse only the
harmless ones.

That question fails **open**, the opposite of this module's default: a path is
refused only when the story that owns it demonstrably evaluates ready. A
contract that cannot be evaluated stays editable, or it could never be repaired.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
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
    frozen: list[dict] = field(default_factory=list)

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
            "frozen": self.frozen,
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
# Contract files of a ready story
# --------------------------------------------------------------------------

def contract_file(config: Config, path: str) -> tuple[str, str] | None:
    """``(story_id, file name)`` when ``path`` is a contract input, else ``None``.

    A path is a contract file by its **location under ``config.stories_dir``**,
    never by its name. ``stories_dir`` is configurable and ``--stories-dir`` can
    point at a corpus outside the git work tree, so the literal prefix
    ``.amigos/stories/`` decides nothing.

    Relative paths are taken against ``config.root``, the same origin
    :func:`classify` already assumes of everything it is handed.
    """
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = config.root / candidate
    try:
        relative = candidate.resolve().relative_to(config.stories_dir.resolve())
    except (ValueError, OSError):
        return None
    if len(relative.parts) != 2:
        return None
    story_id, name = relative.parts
    if name not in story.HASHED_FILES or not story.STORY_ID_RE.match(story_id):
        return None
    return story_id, name


def _git_bytes(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    except OSError as exc:
        raise GateUnavailable(f"git is unavailable: {exc}") from exc
    if result.returncode != 0:
        raise GateUnavailable(f"git {' '.join(args)} failed")
    return result.stdout


def _ready_at_head(config: Config, story_id: str) -> bool:
    """Readiness of the *committed* contract, with the declared state read live.

    At commit time the working tree already holds the edited contract, so
    deriving readiness from it would answer a question about the change using
    the change itself. The four contract inputs therefore come from ``HEAD``.

    ``state.json`` deliberately does not. It is not a contract input file, and
    it is the live control the protocol offers: declaring ``contract_change``
    reopens a contract without having to commit that declaration first.

    A contract absent from ``HEAD`` has never been committed, so there is
    nothing yet to protect and the commit that first records it is permitted.
    """
    from . import verify  # local: verify imports this module.

    directory = config.story_dir(story_id)
    root = verify.work_tree_root(config)
    live_state = directory / "state.json"
    if not live_state.is_file():
        return False

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / story_id
        staging.mkdir()
        for name in story.HASHED_FILES:
            try:
                relative = (directory / name).resolve().relative_to(root).as_posix()
            except ValueError:
                return False
            (staging / name).write_bytes(_git_bytes(root, "show", f"HEAD:{relative}"))
        shutil.copy(live_state, staging / "state.json")
        return dor.evaluate(replace(config, stories_dir=Path(tmp)), story_id).ready


def _ready_before_change(config: Config, story_id: str, staged: bool) -> bool:
    """Did this story's contract evaluate ready *before* the change in hand?

    Fails open. Only a story that demonstrably evaluates ready freezes its
    contract; anything the gate cannot read leaves the contract editable, which
    is what makes a broken contract repairable.
    """
    try:
        if staged:
            return _ready_at_head(config, story_id)
        return dor.evaluate(config, story_id).ready
    except (dor.StructuralError, story.StoryError, GateUnavailable, OSError):
        return False


def frozen_contracts(config: Config, paths: list[str], staged: bool = False) -> list[dict]:
    """The contract files in ``paths`` whose story was ready before the change.

    Each story is evaluated once however many of its files were touched.
    """
    frozen: list[dict] = []
    verdicts: dict[str, bool] = {}
    for path in paths:
        resolved = contract_file(config, path)
        if resolved is None:
            continue
        story_id, name = resolved
        if story_id not in verdicts:
            verdicts[story_id] = _ready_before_change(config, story_id, staged)
        if verdicts[story_id]:
            frozen.append({"path": path, "story_id": story_id, "file": name})
    return frozen


def _frozen_reason(frozen: list[dict]) -> str:
    stories = sorted({entry["story_id"] for entry in frozen})
    listed = ", ".join(sorted({f"{e['story_id']}/{e['file']}" for e in frozen}))
    if len(stories) == 1:
        subject = f"story {stories[0]} is ready and its contract may not be edited"
    else:
        named = ", ".join(stories)
        subject = f"stories {named} are ready and their contracts may not be edited"
    return (
        f"{subject}: {listed}. Reopen it first: "
        f"amigos state {stories[0]} --set contract_change"
    )


# --------------------------------------------------------------------------
# The decision
# --------------------------------------------------------------------------

def decide(
    config: Config,
    paths: list[str],
    override: str | None = None,
    staged: bool = False,
) -> Decision:
    """Decide one change set.

    ``staged`` says where the change lives, which is what decides where the
    *pre-change* contract is read from: the working tree for an edit that has
    not landed, ``HEAD`` for a set already in the index.
    """
    governed, exempt = classify(paths, config)

    frozen = frozen_contracts(config, paths, staged=staged)
    if frozen:
        return Decision(
            permitted=False,
            reason=_frozen_reason(frozen),
            governed=governed, exempt=exempt, frozen=frozen,
        )

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
    return _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRTD")


def working_tree_paths(root: Path) -> list[str]:
    tracked = _git(root, "diff", "--name-only", "--diff-filter=ACMRT")
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))
