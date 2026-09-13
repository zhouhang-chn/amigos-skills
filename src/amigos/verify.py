"""Whether a contract survived its own implementation.

``dor.json`` has recorded a sha256 of each contract input file since v0.1, and
until now nothing read it. This module is that comparison: it re-derives
readiness from the contract files and diffs those files against the hashes the
recorded verdict carries.

Two rules shape it.

Readiness is **recomputed, never read**. ``gate.py`` already works this way, for
the reason stated in its own source: a committed verdict may be stale, and it is
writable by the agent being gated. A second component trusting that file would be
the weak link in a system whose claim is that readiness cannot be self-declared.

The baseline is the recorded hash, **not** the file in git. An agent that edits
the contract and then re-runs ``amigos check`` rewrites the baseline and passes
here. That hole is deliberate: closing it means comparing against history rather
than against the working tree, which is contract immutability, which is v0.6.
What this catches is the case that occurs in practice — a contract edited during
implementation and left behind.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import dor, story
from .config import Config

MATCH = "match"
DIFFERS = "differs"
ABSENT = "absent"

HASHED_FILES = story.HASHED_FILES
BASELINE_FILE = dor.DOR_FILENAME

SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_NOT_VERIFIED = 1


class NoBaseline(dor.StructuralError):
    """No recorded contract hash to compare against.

    A subclass of ``StructuralError`` so it exits 2 like every other structural
    refusal: nothing is wrong with the contract, but the question cannot be
    answered.
    """


@dataclass
class Result:
    story_id: str
    directory: Path
    ready: bool
    state: str
    contract: dict[str, str]
    changed: list[str]

    @property
    def verified(self) -> bool:
        """The milestone's question: ready, and the requirement was not redefined."""
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
            "baseline": BASELINE_FILE,
            "contract": dict(self.contract),
            "changed": list(self.changed),
            "verified": self.verified,
        }


def _baseline(directory: Path) -> dict[str, str]:
    path = directory / BASELINE_FILE
    if not path.is_file():
        raise NoBaseline(
            f"{path}: no recorded contract hash to verify against; "
            "run 'amigos check' on the contract that was agreed"
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NoBaseline(f"{path}: not valid JSON: {exc}") from exc

    recorded = payload.get("contract_hash")
    if not isinstance(recorded, dict) or not recorded:
        raise NoBaseline(f"{path}: no 'contract_hash' recorded; nothing to compare against")
    return {str(k): str(v) for k, v in recorded.items()}


def evaluate(config: Config, story_id: str) -> Result:
    """Re-derive readiness and compare the contract against its recorded hashes.

    Writes nothing. Raises ``StructuralError`` when the story cannot be read at
    all, and ``NoBaseline`` when there is no recorded hash to compare against.
    """
    result = dor.evaluate(config, story_id)
    recorded = _baseline(result.directory)
    current = story.hash_inputs(result.directory)

    contract: dict[str, str] = {}
    changed: list[str] = []
    for name in HASHED_FILES:
        now, before = current.get(name), recorded.get(name)
        if now is None or before is None:
            contract[name] = ABSENT
        elif now == before:
            contract[name] = MATCH
        else:
            contract[name] = DIFFERS
        if contract[name] != MATCH:
            changed.append(name)

    return Result(
        story_id=story_id,
        directory=result.directory,
        ready=result.ready,
        state=result.state,
        contract=contract,
        changed=changed,
    )
