"""STORY-004: recording a lifecycle transition."""

import json

import pytest

from amigos import config as config_module, story
from amigos.cli import main


def read(directory):
    return json.loads((directory / "state.json").read_text())


def test_a_lifecycle_transition_is_recorded(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")
    before = len(read(directory)["history"])

    assert main(["state", "--root", str(scratch_repo), "READY-001",
                 "--set", "amigos_running", "--note", "drafting"]) == 0

    after = read(directory)
    assert after["declared_state"] == "amigos_running"
    assert len(after["history"]) == before + 1
    assert after["history"][-1]["note"] == "drafting"


def test_the_previous_entry_remains_in_the_history(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")
    first = read(directory)["history"][0]

    story.set_state(directory, "amigos_running")
    story.set_state(directory, "contract_change")
    story.set_state(directory, "draft")

    history = read(directory)["history"]
    assert history[0] == first
    assert [h["state"] for h in history[-3:]] == [
        "amigos_running", "contract_change", "draft"]


@pytest.mark.parametrize("declared", ["ready", "blocked"])
def test_the_state_command_refuses_a_state_it_does_not_own(scratch_repo, declared, capsys):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")

    assert main(["state", "--root", str(scratch_repo), "READY-001",
                 "--set", declared]) == 2

    assert read(directory)["declared_state"] == "draft"
    assert "not declarable" in capsys.readouterr().err


def test_an_unknown_state_is_refused(scratch_repo):
    assert main(["state", "--root", str(scratch_repo), "READY-001",
                 "--set", "shipped"]) == 2


def test_a_missing_story_is_reported(scratch_repo, capsys):
    assert main(["state", "--root", str(scratch_repo), "NO-SUCH",
                 "--set", "draft"]) == 2
    assert "story not found" in capsys.readouterr().err


def test_a_withholding_state_keeps_a_complete_contract_from_being_ready(scratch_repo):
    """The reason the skill declares amigos_running while it works."""
    from amigos import dor
    cfg = config_module.load(root=scratch_repo)
    assert dor.evaluate(cfg, "READY-001").ready is True
    story.set_state(cfg.story_dir("READY-001"), "amigos_running")
    result = dor.evaluate(cfg, "READY-001")
    assert result.ready is False
    assert result.state == "amigos_running"


def test_the_timestamp_advances_with_the_transition(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")
    story.set_state(directory, "amigos_running")
    data = read(directory)
    assert data["updated_at"] == data["history"][-1]["at"]
