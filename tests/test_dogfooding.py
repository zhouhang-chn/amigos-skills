"""The project held to its own gate.

README section 31: no change to Amigos Skills may bypass a rule the same version
of Amigos Skills would impose on another project. These tests are that
invariant, expressed as tests.
"""

import json

import pytest

from amigos import dor, jsonschema, story

STORY_IDS = ("STORY-001", "STORY-002", "STORY-003")


@pytest.mark.parametrize("story_id", STORY_IDS)
def test_every_story_in_this_repository_is_ready(repo_config, story_id):
    result = dor.evaluate(repo_config, story_id)
    assert result.ready is True, [f.format() for f in result.failures]


@pytest.mark.parametrize("story_id", STORY_IDS)
def test_the_committed_dor_matches_a_fresh_evaluation(repo_config, story_id):
    """A dor.json edited by hand, or left stale, is caught here."""
    directory = repo_config.story_dir(story_id)
    committed = json.loads((directory / "dor.json").read_text())
    fresh = dor.evaluate(repo_config, story_id).as_dict()
    volatile = {"generated_at"}
    assert {k: v for k, v in committed.items() if k not in volatile} == \
           {k: v for k, v in fresh.items() if k not in volatile}


@pytest.mark.parametrize("story_id", STORY_IDS)
def test_committed_contract_hashes_describe_the_files_on_disk(repo_config, story_id):
    directory = repo_config.story_dir(story_id)
    committed = json.loads((directory / "dor.json").read_text())
    assert committed["contract_hash"] == story.hash_inputs(directory)


@pytest.mark.parametrize("story_id", STORY_IDS)
def test_committed_state_satisfies_its_schema(repo_config, story_id):
    path = repo_config.story_dir(story_id) / "state.json"
    schema = jsonschema.load_schema("state.schema.json")
    assert jsonschema.validate(json.loads(path.read_text()), schema) == []


def test_the_templates_scaffold_a_story_that_is_not_ready(scratch_repo):
    """Phase 0's central claim: a scaffold is visibly unfinished."""
    from amigos import config as config_module
    cfg = config_module.load(root=scratch_repo)
    story.create(cfg, "STORY-999")
    result = dor.evaluate(cfg, "STORY-999")
    assert result.ready is False
    assert result.state == "blocked"


def test_the_readme_vocabulary_is_the_default_vocabulary(repo_root, repo_config):
    """README section 17 and the shipped word list must not drift apart."""
    readme = (repo_root / "README.md").read_text()
    start = readme.index("## 17. Forbidden Acceptance Language")
    block = readme[start:].split("```")[1]
    lines = block.splitlines()[1:]  # drop the fence's info string
    published = [line.strip() for line in lines if line.strip()]
    assert list(repo_config.vague_words) == published
