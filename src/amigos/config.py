"""Repository configuration for amigos-skills.

A repository configures the validator through ``.amigos/config.json``. Every key
is optional; the defaults here are what an unconfigured repository gets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIRNAME = ".amigos"
CONFIG_FILENAME = "config.json"
DEFAULT_STORIES_DIR = ".amigos/stories"

# Exempt from the repository gate. This is exactly the work that makes a story
# ready: gating the contract files would deadlock the protocol, since a story
# could never become ready without editing a story. Everything else is governed,
# including directories that do not exist yet.
DEFAULT_GATE_EXEMPT = (
    ".amigos/**",
    "docs/**",
    "*.md",
    "LICENSE",
    ".gitignore",
)


class ConfigError(Exception):
    """The repository configuration is unusable."""


@dataclass(frozen=True)
class Config:
    """Resolved repository configuration."""

    root: Path
    stories_dir: Path
    vague_words: tuple[str, ...]
    min_primary: int
    min_counterexamples: int
    gate_exempt: tuple[str, ...]
    source: Path | None = field(default=None)

    def story_dir(self, story_id: str) -> Path:
        return self.stories_dir / story_id


def _default_vague_words() -> list[str]:
    text = (Path(__file__).parent / "data" / "vague_words.txt").read_text(encoding="utf-8")
    words = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.append(line)
    return words


def find_root(start: Path | None = None) -> Path | None:
    """Return the nearest ancestor directory containing ``.amigos/``."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / CONFIG_DIRNAME).is_dir():
            return candidate
    return None


def load(root: Path | None = None, stories_dir: Path | None = None) -> Config:
    """Load configuration, falling back to defaults for anything unset.

    ``stories_dir`` overrides both the default and the configured value; it is
    how the CLI points at a fixture corpus outside the repository's own stories.
    """
    resolved_root = (root or find_root() or Path.cwd()).resolve()
    config_path = resolved_root / CONFIG_DIRNAME / CONFIG_FILENAME

    data: dict = {}
    source: Path | None = None
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{config_path}: invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{config_path}: expected a JSON object")
        source = config_path

    lint = data.get("lint") or {}
    dor = data.get("dor") or {}
    gate = data.get("gate") or {}

    words = _default_vague_words()
    removed = {w.strip().lower() for w in lint.get("vague_words_remove", [])}
    words = [w for w in words if w.lower() not in removed]
    for extra in lint.get("vague_words_extra", []):
        if extra.strip() and extra.strip().lower() not in {w.lower() for w in words}:
            words.append(extra.strip())

    if stories_dir is not None:
        resolved_stories = Path(stories_dir)
    else:
        resolved_stories = Path(data.get("stories_dir", DEFAULT_STORIES_DIR))
    if not resolved_stories.is_absolute():
        resolved_stories = resolved_root / resolved_stories

    exempt = gate.get("exempt")
    gate_exempt = tuple(exempt) if isinstance(exempt, list) else DEFAULT_GATE_EXEMPT

    return Config(
        root=resolved_root,
        stories_dir=resolved_stories,
        vague_words=tuple(words),
        min_primary=int(dor.get("min_primary", 1)),
        min_counterexamples=int(dor.get("min_counterexamples", 2)),
        gate_exempt=gate_exempt,
        source=source,
    )
