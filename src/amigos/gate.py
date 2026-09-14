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

STORY-011 added a third question, and it is what stops the second from being
lifted by a text editor. Reopening a frozen contract means declaring
``contract_change`` in ``state.json``, and nothing looked at that file twice: a
declaration written by hand reads exactly like one the protocol produced. So the
gate now asks whether a story's lifecycle record holds together — whether
``declared_state`` and ``updated_at`` are the ones its last history entry
records, and whether the committed history is still a prefix of the current one
— and refuses every governed write for a story whose record does not.

Equality with the committed copy could not carry that rule. ``state.json`` is
*supposed* to move, and a story mid-drafting has uncommitted transitions by
design, so "differs from HEAD" is the normal case here rather than the signal.

Two limits are deliberate. The refusal is a gate decision and never a readiness
verdict: routing it through readiness would invert it, because a story reported
not ready has its contract *released* by the rule above. And a write to a story's
own ``state.json`` stays permitted however broken that record is, because
``set_state()`` parses the file before writing it, so a damaged record could
otherwise never be repaired.

What it cannot catch is a well-formed forgery. There is no key, no signature and
no writer identity, so an appended entry naming a declarable state and a
plausible timestamp is byte-identical to one the command would have written.
This detects an unrecorded change, not hand authorship.
"""

from __future__ import annotations

import json
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

LIFECYCLE_FILE = "state.json"

# Why a lifecycle record does not hold together. The first three are
# statements about the record itself; the fourth is the record being gone.
LIFECYCLE_DECLARATION = "declaration-not-recorded"
LIFECYCLE_TIMESTAMP = "timestamp-not-recorded"
LIFECYCLE_HISTORY = "history-rewritten"
LIFECYCLE_UNREADABLE = "unreadable"

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
    lifecycle: list[dict] = field(default_factory=list)

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
            "lifecycle": self.lifecycle,
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

def story_file(config: Config, path: str) -> tuple[str, str] | None:
    """``(story_id, file name)`` when ``path`` sits directly in a story directory.

    A path belongs to a story by its **location under ``config.stories_dir``**,
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
    if not story.STORY_ID_RE.match(story_id):
        return None
    return story_id, name


def contract_file(config: Config, path: str) -> tuple[str, str] | None:
    """``(story_id, file name)`` when ``path`` is one of the four contract inputs."""
    resolved = story_file(config, path)
    if resolved is None or resolved[1] not in story.HASHED_FILES:
        return None
    return resolved


def lifecycle_file(config: Config, path: str) -> str | None:
    """The story id when ``path`` is that story's ``state.json``, else ``None``."""
    resolved = story_file(config, path)
    if resolved is None or resolved[1] != LIFECYCLE_FILE:
        return None
    return resolved[0]


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
# The lifecycle record
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LifecycleReport:
    """Whether one story's ``state.json`` holds together.

    ``findings`` are ``(rule, message)`` pairs. ``unanswered`` names questions
    git could not answer — a story never committed, or no work tree — which must
    read as neither clean nor tampered.
    """

    story_id: str
    findings: tuple[tuple[str, str], ...] = ()
    unanswered: tuple[str, ...] = ()

    @property
    def unreadable(self) -> bool:
        return any(rule == LIFECYCLE_UNREADABLE for rule, _ in self.findings)

    @property
    def exit_code(self) -> int:
        """0 consistent, 1 inconsistent, 2 could not read.

        An unreadable record exits 2 because that is literally what happened,
        while still refusing at the gate: "I could not tell" must never be a
        cheaper unlock than "I looked".
        """
        if self.unreadable:
            return UNAVAILABLE
        if self.findings:
            return REFUSED
        if self.unanswered:
            return UNAVAILABLE
        return PERMITTED

    def as_dicts(self) -> list[dict]:
        return [{"story_id": self.story_id, "rule": rule, "message": message}
                for rule, message in self.findings]


def _work_tree_relative(config: Config, path: Path) -> tuple[Path, str]:
    from . import verify  # local: verify imports this module.

    root = verify.work_tree_root(config)
    try:
        return root, path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise GateUnavailable(f"{path} is outside the work tree") from exc


def _record_bytes(config: Config, directory: Path, staged: bool) -> bytes:
    """The record as the change in hand would leave it.

    For a staged set that is the index, so a rewritten ``state.json`` is judged
    on what is about to be committed rather than on what happens to be on disk.
    A file the index does not track falls back to disk.
    """
    path = directory / LIFECYCLE_FILE
    if staged:
        try:
            root, relative = _work_tree_relative(config, path)
            return _git_bytes(root, "show", f":{relative}")
        except GateUnavailable:
            pass
    if not path.is_file():
        raise GateUnavailable(f"{path}: missing")
    return path.read_bytes()


def _history_of(payload: dict) -> list[dict]:
    history = payload.get("history")
    if not isinstance(history, list):
        return []
    return [item for item in history if isinstance(item, dict)]


def _internal_findings(payload: dict) -> list[tuple[str, str]]:
    """What ``set_state()`` guarantees, checked against what the file says."""
    declared = payload.get("declared_state")
    history = _history_of(payload)
    if not history:
        return [(LIFECYCLE_DECLARATION,
                 f"{LIFECYCLE_FILE} declares {declared!r}, which its history does "
                 f"not record: the history is empty")]

    findings: list[tuple[str, str]] = []
    last = history[-1]
    if last.get("state") != declared:
        findings.append((
            LIFECYCLE_DECLARATION,
            f"{LIFECYCLE_FILE} declares {declared!r}, which its history does not "
            f"record; the last entry records {last.get('state')!r} "
            f"at {last.get('at')}",
        ))
    if last.get("at") != payload.get("updated_at"):
        findings.append((
            LIFECYCLE_TIMESTAMP,
            f"{LIFECYCLE_FILE} updated_at {payload.get('updated_at')!r} is not the "
            f"time its last history entry records ({last.get('at')!r})",
        ))
    return findings


def _history_findings(committed: list[dict], current: list[dict]) -> list[tuple[str, str]]:
    """The committed history must still be a prefix of the current one.

    Equality cannot carry this rule: ``state.json`` is supposed to gain entries,
    and a story mid-drafting has uncommitted transitions by design.
    """
    for index, past in enumerate(committed):
        if index >= len(current) or current[index] != past:
            return [(LIFECYCLE_HISTORY,
                     f"{LIFECYCLE_FILE} no longer records the {past.get('state')!r} "
                     f"entry committed at {past.get('at')}")]
    return []


def lifecycle_report(config: Config, story_id: str, staged: bool = False) -> LifecycleReport:
    """Does this story's lifecycle record hold together?

    Writes nothing, and never consults ``dor.json``: this asks about the record
    an agent writes, not about the verdict derived from it.
    """
    directory = config.story_dir(story_id)
    if not directory.is_dir():
        # Not a story at all, so there is no record here that could fail to hold
        # together. STORY-010 already decided that a contract which cannot be
        # evaluated stays editable; this must not quietly reverse that.
        return LifecycleReport(story_id, (), ("there is no such story directory",))

    try:
        payload = json.loads(_record_bytes(config, directory, staged))
        if not isinstance(payload, dict):
            raise ValueError("expected a JSON object")
    except (GateUnavailable, OSError, ValueError) as exc:
        return LifecycleReport(
            story_id,
            ((LIFECYCLE_UNREADABLE, f"{LIFECYCLE_FILE} cannot be read: {exc}"),),
        )

    if payload.get("declared_state") not in story.DECLARABLE_STATES:
        # Refused upstream by story.read_state(), in more precise words than
        # this rule could offer: declaring a state you do not own is a louder
        # failure than declaring one your history does not record, and it
        # already has an implementation. One rule, one implementation.
        return LifecycleReport(
            story_id, (),
            (f"{LIFECYCLE_FILE} declares "
             f"{payload.get('declared_state')!r}, which is not declarable",))

    findings = _internal_findings(payload)
    try:
        root, relative = _work_tree_relative(config, directory / LIFECYCLE_FILE)
        committed = _history_of(json.loads(_git_bytes(root, "show", f"HEAD:{relative}")))
    except (GateUnavailable, OSError, ValueError):
        return LifecycleReport(
            story_id, tuple(findings),
            (f"{LIFECYCLE_FILE} has no committed copy to compare against",),
        )
    return LifecycleReport(
        story_id, tuple(findings + _history_findings(committed, _history_of(payload))))


def lifecycle_refusals(
    config: Config,
    paths: list[str],
    override: str | None = None,
    staged: bool = False,
) -> list[dict]:
    """The stories in this change whose lifecycle record refuses it.

    A story is implicated strictly when the change touches its contract or when
    it is the resolved story for a governed path. It is implicated *leniently*
    when the only thing touched is its own ``state.json`` — that write is how a
    damaged record gets repaired, since ``set_state()`` parses the file before
    writing it. Erasing committed history is never repair, so that one finding
    refuses either way.
    """
    strict: dict[str, bool] = {}
    governed, _ = classify(paths, config)

    for path in paths:
        contract = contract_file(config, path)
        if contract is not None:
            strict[contract[0]] = True
            continue
        named = lifecycle_file(config, path)
        if named is not None:
            strict.setdefault(named, False)

    if governed:
        story_id, _, _ = resolve_story(config, override)
        if story_id is not None:
            strict[story_id] = True

    refusals: list[dict] = []
    for story_id, is_strict in strict.items():
        report = lifecycle_report(config, story_id, staged=staged)
        offending = report.findings if is_strict else tuple(
            finding for finding in report.findings if finding[0] == LIFECYCLE_HISTORY)
        refusals.extend({"story_id": story_id, "rule": rule, "message": message}
                        for rule, message in offending)
    return refusals


def _lifecycle_reason(refusals: list[dict]) -> str:
    stories = sorted({entry["story_id"] for entry in refusals})
    detail = "; ".join(entry["message"] for entry in refusals[:3])
    if len(stories) == 1:
        subject = f"story {stories[0]}'s lifecycle record does not hold together"
    else:
        subject = (f"the lifecycle records of {', '.join(stories)} "
                   "do not hold together")
    return f"{subject}: {detail}"


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

    # Asked first: the freeze below reads state.json live, so a record that does
    # not hold together makes that verdict untrustworthy rather than merely
    # inconvenient.
    lifecycle = lifecycle_refusals(config, paths, override=override, staged=staged)
    if lifecycle:
        return Decision(
            permitted=False,
            reason=_lifecycle_reason(lifecycle),
            governed=governed, exempt=exempt, lifecycle=lifecycle,
        )

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
