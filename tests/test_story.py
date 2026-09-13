import json

import pytest

from amigos import config as config_module, story


def test_scaffold_writes_every_contract_input(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = story.create(cfg, "STORY-999")
    assert sorted(p.name for p in directory.iterdir()) == sorted(story.INPUT_FILES)


def test_scaffold_declares_draft_and_writes_no_dor(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = story.create(cfg, "STORY-999")
    assert story.read_state(directory).declared_state == "draft"
    assert not (directory / "dor.json").exists()


def test_scaffold_substitutes_the_story_id(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = story.create(cfg, "STORY-999")
    state = json.loads((directory / "state.json").read_text())
    assert state["story_id"] == "STORY-999"
    assert "__STORY_ID__" not in (directory / "state.json").read_text()
    assert "__TIMESTAMP__" not in (directory / "state.json").read_text()


def test_scaffold_refuses_to_overwrite_and_changes_nothing(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    with pytest.raises(story.StoryError) as excinfo:
        story.create(cfg, "READY-001")
    assert "refusing to overwrite" in str(excinfo.value)
    after = {p.name: p.read_bytes() for p in directory.iterdir()}
    assert after == before


@pytest.mark.parametrize("story_id", ["", "../escape", "has space", "9leading", "a/b"])
def test_malformed_story_ids_are_rejected(story_id):
    with pytest.raises(story.StoryError):
        story.validate_story_id(story_id)


def test_missing_inputs_lists_names_in_canonical_order(fixture_config):
    directory = fixture_config.story_dir("MISSING-001")
    assert story.missing_inputs(directory) == ["constraints.md"]


def test_an_agent_cannot_declare_ready(fixture_config):
    directory = fixture_config.story_dir("SELFPROMO-001")
    with pytest.raises(story.StoryError) as excinfo:
        story.read_state(directory)
    assert "not declarable" in str(excinfo.value)


def test_an_agent_cannot_declare_blocked(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")
    path = directory / "state.json"
    data = json.loads(path.read_text())
    data["declared_state"] = "blocked"
    path.write_text(json.dumps(data))
    with pytest.raises(story.StoryError) as excinfo:
        story.read_state(directory)
    assert "not declarable" in str(excinfo.value)


def test_unknown_declared_state_is_rejected(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    path = cfg.story_dir("READY-001") / "state.json"
    path.write_text(json.dumps({"declared_state": "shipped"}))
    with pytest.raises(story.StoryError) as excinfo:
        story.read_state(path.parent)
    assert "unknown declared_state" in str(excinfo.value)


def test_readiness_is_absent_from_the_declarable_states():
    assert "ready" not in story.DECLARABLE_STATES
    assert "blocked" not in story.DECLARABLE_STATES


def test_hashes_cover_every_input_except_the_lifecycle_file(fixture_config):
    digests = story.hash_inputs(fixture_config.story_dir("READY-001"))
    assert set(digests) == set(story.HASHED_FILES)
    assert "state.json" not in digests
    assert all(v.startswith("sha256:") for v in digests.values())


def test_hashes_change_when_a_contract_file_changes(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    directory = cfg.story_dir("READY-001")
    before = story.hash_inputs(directory)
    path = directory / "acceptance.feature"
    path.write_text(path.read_text() + "\n# a trailing comment\n")
    assert story.hash_inputs(directory)["acceptance.feature"] != before["acceptance.feature"]
