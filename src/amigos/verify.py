"""Whether a contract survived its own implementation.

v0.5 answered this by hashing the four contract files in the working tree
against ``dor.json.contract_hash``. Both sides of that comparison are writable
by the agent being judged, and ``amigos check`` rewrites the recorded side on
every run — a command ``/implement``'s own Phase 0 executes. The check did not
fail; it was answered by erasing the question.

STORY-009 moves the baseline into git history.

The baseline is **the parent of the earliest commit that changes a governed path
for this story**. A contract edit committed during implementation is newer than
that commit, so it cannot become the baseline — which is what separates this
from comparing against the latest commit, where an ordinary ``git commit``
launders the edit exactly as ``amigos check`` used to.

Two rules carry over unchanged.

Readiness is **recomputed, never read**. ``gate.py`` works this way for the
reason stated in its own source: a committed verdict may be stale, and it is
writable by the agent being gated.

A question that **could not be answered never reads as verified**. Exit 2 covers
an absent work tree, absent git, and a contract that was never committed; it is
kept distinct from exit 1, which means the question was put and the answer was
no.

``dor.json.contract_hash`` is left in place. It is required by the schema, is
present in every committed ``dor.json``, and is still the only answer available
in a checkout without git. It is a record; history is the authority.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import dor, gate, story
from .config import Config

MATCH = "match"
DIFFERS = "differs"
ABSENT = "absent"

HASHED_FILES = story.HASHED_FILES
RECORDED_BASELINE_FILE = dor.DOR_FILENAME

SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_NOT_VERIFIED = 1


class NoBaseline(dor.StructuralError):
    """No committed contract to compare against.

    A subclass of ``StructuralError`` so it exits 2 like every other structural
    refusal: nothing is wrong with the contract, but the question cannot be put.
    """


@dataclass
class Result:
    story_id: str
    directory: Path
    ready: bool
    state: str
    baseline: str
    contract: dict[str, str]
    changed: list[str]

    @property
    def verified(self) -> bool:
        """The question: ready, and the requirement was not redefined."""
        return self.ready and not self.changed

    @property
    def exit_code(self) -> int:
        return EXIT_OK if self.verified else EXIT_NOT_VERIFIED

    def as_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "story_id": self.story_id,
            "ready": self.ready,
            "state": self.state,
            "baseline": self.baseline,
            "contract": dict(self.contract),
            "changed": list(self.changed),
            "verified": self.verified,
        }


# --------------------------------------------------------------------------
# git
# --------------------------------------------------------------------------

def _git(root: Path, *args: str) -> str:
    """Run git, or raise ``NoBaseline`` when it cannot answer.

    Every git-side failure lands on exit 2 by decision. "I could not tell" and
    "the contract moved" need different responses from a human.
    """
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        raise NoBaseline(f"git is unavailable: {exc}") from exc
    if result.returncode != 0:
        raise NoBaseline(
            f"git {' '.join(args)} failed: {result.stderr.strip() or 'unknown error'}"
        )
    return result.stdout.strip()


def _lines(root: Path, *args: str) -> list[str]:
    return [line for line in _git(root, *args).splitlines() if line.strip()]


def work_tree_root(config: Config) -> Path:
    """The git work-tree root, which need not be ``config.root``.

    ``config.root`` is the nearest ancestor holding ``.amigos/``, and
    ``--stories-dir`` can point at a corpus outside the work tree entirely. Paths
    handed to git must be relative to this, not to that.
    """
    return Path(_git(config.root, "rev-parse", "--show-toplevel")).resolve()


def _tracked_paths(config: Config, directory: Path) -> dict[str, str]:
    """Map each contract file name to its path relative to the work-tree root."""
    root = work_tree_root(config)
    paths: dict[str, str] = {}
    for name in HASHED_FILES:
        try:
            paths[name] = (directory / name).resolve().relative_to(root).as_posix()
        except ValueError as exc:
            raise NoBaseline(
                f"{directory / name} lies outside the git work tree at {root}; "
                "the contract cannot be compared against history"
            ) from exc
    return paths


def _governed_in(config: Config, root: Path, revision: str) -> bool:
    """Did this commit change a path the gate governs?

    Governed is ``gate.classify()`` and not a second definition of the same
    thing, because two definitions of one rule drift.
    """
    changed = _lines(
        config.root, "diff-tree", "--no-commit-id", "--name-only", "-r", revision,
    )
    relative = []
    for path in changed:
        absolute = (root / path).resolve()
        try:
            relative.append(absolute.relative_to(config.root).as_posix())
        except ValueError:
            relative.append(path)
    governed, _ = gate.classify(relative, config)
    return bool(governed)


def baseline_revision(config: Config, story_id: str) -> str:
    """The revision this story's contract is judged against.

    The parent of the earliest commit that changes a governed path for this
    story. When implementation has not been committed yet there is nothing to
    have redefined the requirement, and the baseline is the current commit.
    """
    directory = config.story_dir(story_id)
    root = work_tree_root(config)
    paths = list(_tracked_paths(config, directory).values())

    contract_commits = _lines(config.root, "rev-list", "HEAD", "--", *paths)
    if not contract_commits:
        raise NoBaseline(
            f"no committed contract was found for {story_id}: none of its four "
            "contract files appear in any commit reachable from HEAD. Commit the "
            "contract before implementing against it."
        )
    first_contract = contract_commits[-1]

    for revision in _lines(config.root, "rev-list", "--reverse", f"{first_contract}..HEAD"):
        if _governed_in(config, root, revision):
            return _git(config.root, "rev-parse", f"{revision}^")

    return _git(config.root, "rev-parse", "HEAD")


# --------------------------------------------------------------------------
# The comparison
# --------------------------------------------------------------------------

def recorded_hashes(directory: Path) -> dict[str, str]:
    """The hashes ``dor.json`` records. A record, no longer the authority."""
    path = directory / RECORDED_BASELINE_FILE
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    recorded = payload.get("contract_hash")
    if not isinstance(recorded, dict):
        return {}
    return {str(k): str(v) for k, v in recorded.items()}


def evaluate(config: Config, story_id: str) -> Result:
    """Re-derive readiness and compare the contract against its committed baseline.

    Writes nothing. Raises ``StructuralError`` when the story cannot be read at
    all, and ``NoBaseline`` when there is no committed contract to compare
    against.
    """
    result = dor.evaluate(config, story_id)
    revision = baseline_revision(config, story_id)
    paths = _tracked_paths(config, result.directory)

    # Ask git for the difference rather than comparing bytes to a blob. Under
    # core.autocrlf or any clean filter those are not the same question, and a
    # repository with no .gitattributes never reveals the difference.
    differing = set(_lines(
        config.root, "diff", "--name-only", revision, "--", *paths.values(),
    ))

    contract: dict[str, str] = {}
    changed: list[str] = []
    for name, relative in paths.items():
        if not (result.directory / name).is_file():
            contract[name] = ABSENT
        elif relative in differing:
            contract[name] = DIFFERS
        else:
            contract[name] = MATCH
        if contract[name] != MATCH:
            changed.append(name)

    return Result(
        story_id=story_id,
        directory=result.directory,
        ready=result.ready,
        state=result.state,
        baseline=revision,
        contract=contract,
        changed=changed,
    )
