import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from amigos import config as config_module  # noqa: E402

FIXTURE_STORIES = Path(__file__).parent / "fixtures" / "stories"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def fixture_config():
    """Configuration pointing at the read-only fixture corpus."""
    return config_module.load(root=REPO_ROOT, stories_dir=FIXTURE_STORIES)


@pytest.fixture
def repo_config():
    """Configuration for this repository's own stories."""
    return config_module.load(root=REPO_ROOT)


@pytest.fixture
def scratch_repo(tmp_path: Path) -> Path:
    """An initialised repository with a writable copy of the fixture corpus."""
    (tmp_path / ".amigos").mkdir()
    shutil.copy(REPO_ROOT / ".amigos" / "config.json", tmp_path / ".amigos" / "config.json")
    shutil.copytree(FIXTURE_STORIES, tmp_path / ".amigos" / "stories")
    shutil.copytree(REPO_ROOT / "templates", tmp_path / "templates")
    return tmp_path


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


@pytest.fixture
def git_repo(scratch_repo: Path) -> Path:
    """An initialised repository under git, on a branch naming no story."""
    _git(scratch_repo, "init", "-q", "-b", "work")
    _git(scratch_repo, "config", "user.email", "test@example.invalid")
    _git(scratch_repo, "config", "user.name", "Test")
    _git(scratch_repo, "add", "-A")
    _git(scratch_repo, "commit", "-q", "-m", "baseline")
    return scratch_repo


@pytest.fixture
def on_branch(git_repo: Path):
    """Switch the scratch repository to a named branch."""
    def switch(name: str) -> Path:
        _git(git_repo, "switch", "-q", "-c", name)
        return git_repo
    return switch


@pytest.fixture(autouse=True)
def no_ambient_story(monkeypatch):
    """The environment must never leak an active story into a test."""
    monkeypatch.delenv("AMIGOS_STORY", raising=False)
