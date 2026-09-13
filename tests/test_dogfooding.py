"""The project held to its own gate.

README section 31: no change to Amigos Skills may bypass a rule the same version
of Amigos Skills would impose on another project. These tests are that
invariant, expressed as tests.
"""

import json

import pytest

from amigos import dor, jsonschema, story

STORY_IDS = ("STORY-001", "STORY-002", "STORY-003", "STORY-004",
             "STORY-005", "STORY-007")


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


def test_this_repository_governs_its_own_source(repo_config):
    """The gate's exempt set must not quietly stop governing the code."""
    from amigos import gate
    for governed in ("src/amigos/dor.py", "scripts/check_dor.py", "tests/test_dor.py",
                     "pyproject.toml", "integrations/claude-code/gate_hook.py"):
        assert not gate.is_exempt(governed, repo_config.gate_exempt), governed


def test_this_repository_exempts_the_work_that_makes_a_story_ready(repo_config):
    """Gating the contract files would deadlock the protocol."""
    from amigos import gate
    for exempt in (".amigos/stories/STORY-007/intent.md", ".amigos/config.json",
                   "docs/versions/v0.2-repository-gate/design.md", "README.md"):
        assert gate.is_exempt(exempt, repo_config.gate_exempt), exempt


def test_a_generated_contract_passes_the_same_gate_as_a_hand_authored_one(repo_config):
    """v0.3's success criterion, kept as a regression.

    STORY-005's contract was produced by running the amigos skill, not by hand.
    It is held to exactly the checks every hand-authored contract is held to.
    """
    from amigos import dor
    result = dor.evaluate(repo_config, "STORY-005")
    assert result.ready is True, [f.format() for f in result.failures]
    assert result.scenarios["primary"] >= repo_config.min_primary
    assert result.scenarios["counterexample"] >= repo_config.min_counterexamples


def test_the_skill_run_left_a_lifecycle_trail(repo_config):
    """A run declares amigos_running while it works and returns the story to draft."""
    import json
    path = repo_config.story_dir("STORY-005") / "state.json"
    states = [entry["state"] for entry in json.loads(path.read_text())["history"]]
    assert "amigos_running" in states
    assert states[-1] == "draft"
