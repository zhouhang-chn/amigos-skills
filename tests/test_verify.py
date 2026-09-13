"""STORY-006: the command that decides whether the requirement was redefined.

`dor.json` has recorded a sha256 of each contract input file since v0.1 and
nothing has ever read it. These tests hold the comparison that reads it, and the
rule that makes it worth having: readiness is re-derived from the contract files,
never taken from the verdict recorded beside them.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from amigos import config as config_module, dor, verify

FIXTURES = Path(__file__).parent / "fixtures" / "stories"


@pytest.fixture
def baselined(git_repo: Path):
    """A story whose contract is committed, and so has a baseline in history.

    STORY-009 moved the baseline from ``dor.json.contract_hash`` into git, so
    the fixture that establishes one is now a commit rather than a write. The
    assertions below are unchanged: what they hold is that readiness is
    re-derived and that a moved contract is named, neither of which depends on
    where the baseline is kept.
    """
    def prepare(story_id: str = "READY-001"):
        cfg = config_module.load(root=git_repo)
        dor.write(dor.evaluate(cfg, story_id))
        subprocess.run(["git", "add", "-A"], cwd=git_repo, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "contract"], cwd=git_repo,
                       check=True, capture_output=True)
        return cfg, story_id
    return prepare


def test_an_untouched_contract_verifies(baselined):
    cfg, story_id = baselined()
    result = verify.evaluate(cfg, story_id)

    assert result.ready is True
    assert result.changed == []
    assert result.verified is True
    assert result.exit_code == verify.EXIT_OK


def test_an_edited_contract_names_the_file_that_differs(baselined, scratch_repo):
    cfg, story_id = baselined()
    feature = scratch_repo / ".amigos" / "stories" / story_id / "acceptance.feature"
    feature.write_text(feature.read_text() + "\n# edited after the baseline\n")

    result = verify.evaluate(cfg, story_id)

    assert result.changed == ["acceptance.feature"]
    assert result.contract["acceptance.feature"] == verify.DIFFERS
    assert result.contract["intent.md"] == verify.MATCH
    assert result.verified is False
    assert result.exit_code == verify.EXIT_NOT_VERIFIED


def test_every_edited_file_is_named_not_just_the_first(baselined, scratch_repo):
    cfg, story_id = baselined()
    directory = scratch_repo / ".amigos" / "stories" / story_id
    for name in ("intent.md", "constraints.md"):
        path = directory / name
        path.write_text(path.read_text() + "\n<!-- edited -->\n")

    result = verify.evaluate(cfg, story_id)

    assert result.changed == ["intent.md", "constraints.md"]


def test_a_stale_ready_verdict_never_produces_a_pass(baselined, scratch_repo):
    """The failure this command exists to prevent: an agent-writable verdict."""
    cfg, story_id = baselined()
    directory = scratch_repo / ".amigos" / "stories" / story_id

    # Break the contract, then hand-edit dor.json to keep claiming readiness.
    feature = directory / "acceptance.feature"
    feature.write_text(feature.read_text().replace("@counterexample", "@primary", 1))
    payload = json.loads((directory / "dor.json").read_text())
    payload["ready"] = True
    payload["state"] = "ready"
    (directory / "dor.json").write_text(json.dumps(payload, indent=2))

    result = verify.evaluate(cfg, story_id)

    assert result.ready is False, "readiness must be re-derived, not read"
    assert result.verified is False
    assert result.exit_code != verify.EXIT_OK


def test_readiness_comes_from_the_contract_when_dor_says_otherwise(baselined, scratch_repo):
    """A dor.json claiming not-ready does not override a contract that is ready."""
    cfg, story_id = baselined()
    directory = scratch_repo / ".amigos" / "stories" / story_id
    payload = json.loads((directory / "dor.json").read_text())
    payload["ready"] = False
    payload["state"] = "blocked"
    (directory / "dor.json").write_text(json.dumps(payload, indent=2))

    result = verify.evaluate(cfg, story_id)

    assert result.ready is True
    assert result.verified is True


def test_a_story_that_is_not_ready_does_not_verify(baselined):
    cfg, story_id = baselined("BLOCKED-001")

    result = verify.evaluate(cfg, story_id)

    assert result.ready is False
    assert result.changed == []
    assert result.verified is False
    assert result.exit_code == verify.EXIT_NOT_VERIFIED


def test_no_baseline_is_a_structural_error(scratch_repo):
    """Superseded mechanism, same meaning.

    Under v0.5 "no baseline" meant an absent ``dor.json``. STORY-009 made it an
    absent commit, so this holds the same refusal against the new cause.
    """
    cfg = config_module.load(root=scratch_repo)
    with pytest.raises(verify.NoBaseline):
        verify.evaluate(cfg, "READY-001")


def test_a_recorded_hash_is_no_longer_required_to_verify(baselined, scratch_repo):
    """STORY-009 demoted ``contract_hash`` from authority to record.

    Deleting it used to make verification structurally impossible. It no longer
    does, because the answer now comes from history.
    """
    cfg, story_id = baselined()
    path = scratch_repo / ".amigos" / "stories" / story_id / "dor.json"
    payload = json.loads(path.read_text())
    del payload["contract_hash"]
    path.write_text(json.dumps(payload, indent=2))

    assert verify.recorded_hashes(cfg.story_dir(story_id)) == {}
    assert verify.evaluate(cfg, story_id).verified is True


def test_a_structurally_unusable_story_propagates(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    with pytest.raises(dor.StructuralError):
        verify.evaluate(cfg, "MISSING-001")


def test_verify_writes_nothing(baselined, scratch_repo):
    cfg, story_id = baselined()
    directory = scratch_repo / ".amigos" / "stories" / story_id
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}

    verify.evaluate(cfg, story_id)

    after = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    assert after == before


def test_the_result_serialises_for_a_json_caller(baselined):
    cfg, story_id = baselined()
    payload = verify.evaluate(cfg, story_id).as_dict()

    assert payload["story_id"] == story_id
    assert len(payload["baseline"]) == 40, "the baseline is a git revision"
    assert payload["verified"] is True
    assert set(payload["contract"]) == set(verify.HASHED_FILES)
