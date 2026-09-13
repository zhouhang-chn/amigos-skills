"""STORY-009: the contract a story is judged against lives in git history.

v0.5 shipped `verify` comparing the working tree against a hash recorded in
`dor.json` — a field `amigos check` rewrites on every run, which `/implement`'s
own Phase 0 runs. Both sides of that comparison are writable by the agent being
judged.

These tests hold the replacement. The baseline is the parent of the earliest
commit that changes a governed path for the story, so a contract edit committed
during implementation is newer than the baseline and cannot become it.

One scenario per test, named for the scenario in
`.amigos/stories/STORY-009/acceptance.feature`.
"""

import json
import subprocess
from pathlib import Path

import pytest

from amigos import config as config_module, verify

STORY = "READY-001"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


@pytest.fixture
def contracted(git_repo: Path):
    """A repository whose story contract is committed, and helpers to move on.

    `git_repo` commits the whole fixture corpus as "baseline", so the contract
    is already in history. What these tests need on top is the ability to make
    the next two commits the baseline derivation turns on: a governed change,
    and then a contract edit.
    """
    root = git_repo
    story_dir = root / ".amigos" / "stories" / STORY

    class Repo:
        root = git_repo
        directory = story_dir

        @property
        def config(self):
            return config_module.load(root=root)

        def head(self) -> str:
            return _git(root, "rev-parse", "HEAD")

        def commit_governed(self, message: str = "implementation") -> str:
            """Commit a change to a governed path, i.e. start implementing."""
            source = root / "src" / "thing.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                (source.read_text() if source.exists() else "") + f"# {message}\n"
            )
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", message)
            return self.head()

        def edit_contract(self, name: str = "acceptance.feature") -> Path:
            path = story_dir / name
            path.write_text(path.read_text() + "\n# edited during implementation\n")
            return path

        def commit_all(self, message: str) -> str:
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", message)
            return self.head()

    return Repo()


# --------------------------------------------------------------------------
# @primary
# --------------------------------------------------------------------------

def test_an_unchanged_contract_verifies_against_its_committed_baseline(contracted):
    """The exit code is 0, verified is true, and the revision is named."""
    result = verify.evaluate(contracted.config, STORY)

    assert result.verified is True
    assert result.exit_code == verify.EXIT_OK
    assert result.changed == []
    assert result.baseline, "the revision compared against is not reported"


def test_the_baseline_names_the_revision_in_its_serialised_form(contracted):
    """A JSON caller sees which revision the comparison used."""
    payload = verify.evaluate(contracted.config, STORY).as_dict()

    assert payload["baseline"] == contracted.head()


def test_verify_writes_no_file_inside_the_story_directory(contracted):
    before = {
        p.name: p.read_bytes()
        for p in contracted.directory.iterdir() if p.is_file()
    }
    names_before = set(before)

    verify.evaluate(contracted.config, STORY)

    after = {
        p.name: p.read_bytes()
        for p in contracted.directory.iterdir() if p.is_file()
    }
    assert set(after) == names_before
    assert after == before


def test_the_baseline_is_the_parent_of_the_first_governed_change(contracted):
    """The load-bearing choice: not HEAD, but where implementation began."""
    contract_commit = contracted.head()
    first_governed = contracted.commit_governed("first governed change")
    contracted.commit_governed("more implementation")

    baseline = verify.baseline_revision(contracted.config, STORY)

    assert baseline == _git(contracted.root, "rev-parse", f"{first_governed}^")
    assert baseline == contract_commit


# --------------------------------------------------------------------------
# @counterexample
# --------------------------------------------------------------------------

def test_re_running_the_readiness_check_does_not_launder_a_contract_edit(contracted):
    """The hole v0.5 documented and handed to v0.6, closed."""
    from amigos import dor

    contracted.commit_governed("implementation has begun")
    contracted.edit_contract()

    before = verify.evaluate(contracted.config, STORY)
    dor.write(dor.evaluate(contracted.config, STORY))   # the laundering attempt
    after = verify.evaluate(contracted.config, STORY)

    assert after.exit_code == verify.EXIT_NOT_VERIFIED
    assert "acceptance.feature" in after.changed
    assert after.changed == before.changed, "re-running check changed the verdict"


def test_a_committed_contract_edit_does_not_become_the_baseline(contracted):
    """A commit is an ordinary action, so it must not move the baseline."""
    contracted.commit_governed("implementation has begun")
    contracted.edit_contract()
    contracted.commit_all("sneak the contract edit into history")

    result = verify.evaluate(contracted.config, STORY)

    assert result.exit_code == verify.EXIT_NOT_VERIFIED
    assert "acceptance.feature" in result.changed


def test_a_contract_that_was_never_committed_is_unanswerable(contracted):
    """Exit 2, not 1: nothing is wrong with the contract, the question cannot be put."""
    import shutil

    uncommitted = contracted.directory.parent / "UNCOMMITTED-001"
    shutil.copytree(contracted.directory, uncommitted)

    with pytest.raises(verify.NoBaseline) as caught:
        verify.evaluate(contracted.config, "UNCOMMITTED-001")

    assert "no committed contract" in str(caught.value)


def test_a_checkout_without_git_is_unanswerable_too(scratch_repo):
    """constraints.md: every git-side failure lands on an exit code by decision."""
    cfg = config_module.load(root=scratch_repo)

    with pytest.raises(verify.NoBaseline):
        verify.evaluate(cfg, STORY)


def test_a_readiness_verdict_written_by_hand_produces_no_pass(contracted):
    """Readiness stays re-derived even when the baseline moved to git."""
    from amigos import dor

    feature = contracted.directory / "acceptance.feature"
    kept = [
        block for block in feature.read_text().split("\n\n")
        if "@counterexample" not in block
    ]
    feature.write_text("\n\n".join(kept))

    path = contracted.directory / dor.DOR_FILENAME
    payload = json.loads(path.read_text()) if path.is_file() else {}
    payload.update({"ready": True, "state": "ready"})
    path.write_text(json.dumps(payload, indent=2))

    result = verify.evaluate(contracted.config, STORY)

    assert result.ready is False
    assert result.exit_code == verify.EXIT_NOT_VERIFIED


def test_a_change_outside_the_story_directory_is_not_a_contract_change(contracted):
    (contracted.root / "src").mkdir(exist_ok=True)
    (contracted.root / "src" / "uncommitted.py").write_text("# not a contract\n")
    (contracted.root / "tests").mkdir(exist_ok=True)
    (contracted.root / "tests" / "test_uncommitted.py").write_text("# nor this\n")

    result = verify.evaluate(contracted.config, STORY)

    assert result.exit_code == verify.EXIT_OK
    assert result.verified is True
    for name in result.contract:
        assert (contracted.directory / name).is_file(), name


def test_a_contract_rewritten_through_contract_change_stays_verifiable(contracted):
    """The legitimate path must not deadlock: re-contract, commit, verify."""
    superseded = (contracted.directory / "intent.md").read_text()

    path = contracted.edit_contract("intent.md")
    rewritten = path.read_text()
    contracted.commit_all("contract rewritten after contract_change")

    result = verify.evaluate(contracted.config, STORY)
    assert result.exit_code == verify.EXIT_OK, result.changed

    path.write_text(superseded)
    assert verify.evaluate(contracted.config, STORY).exit_code == \
        verify.EXIT_NOT_VERIFIED

    path.write_text(rewritten)


def test_a_configured_content_filter_does_not_produce_a_difference(contracted):
    """Byte equality against a blob is not git equality under a filter."""
    _git(contracted.root, "config", "core.autocrlf", "true")
    (contracted.root / ".gitattributes").write_text("* text=auto\n")
    contracted.commit_all("configure line-ending normalisation")

    path = contracted.directory / "acceptance.feature"
    path.write_bytes(path.read_text().replace("\n", "\r\n").encode())

    result = verify.evaluate(contracted.config, STORY)

    assert result.exit_code == verify.EXIT_OK, result.changed
