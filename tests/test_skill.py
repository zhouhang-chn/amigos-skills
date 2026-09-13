"""STORY-004: the discipline the skill states.

A prompt cannot be unit tested for behaviour, but it can be held to the rules it
is supposed to carry. These tests fail when the instructions drift away from what
the code enforces, which is the drift that matters: the skill telling an agent to
do something the validator forbids, or omitting a rule nothing else enforces.
"""

from pathlib import Path

import pytest

from amigos import dor, story
from amigos.config import _default_vague_words

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "amigos" / "SKILL.md"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_the_skill_ships_where_the_plugin_declares_it():
    import json
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["skills"] == "./skills"
    assert SKILL.is_file()


def test_this_checkout_discovers_the_same_file_the_plugin_ships():
    link = REPO_ROOT / ".claude" / "skills" / "amigos"
    assert link.is_symlink(), "the checkout should not hold a second copy"
    assert (link / "SKILL.md").resolve() == SKILL.resolve()


def test_the_skill_declares_frontmatter(skill_text):
    assert skill_text.startswith("---\n")
    front = skill_text.split("---", 2)[1]
    assert "name: amigos" in front
    assert "description:" in front


def test_the_skill_forbids_writing_the_derived_verdict(skill_text):
    assert "dor.json" in skill_text
    assert "Write or edit `dor.json`" in skill_text


def test_the_skill_forbids_declaring_readiness(skill_text):
    assert "Declare `ready` or `blocked` in `state.json`" in skill_text


def test_the_skill_forbids_inventing_an_assumption(skill_text):
    assert "Invent an assumption to clear a blocking question" in skill_text
    assert "Prefer a blocked story over invented certainty" in skill_text


def test_the_skill_bounds_both_of_its_loops(skill_text):
    assert "at most two rounds" in skill_text.lower()
    assert "at most three attempts" in skill_text.lower()


def test_the_skill_names_every_vague_word_the_linter_rejects(skill_text):
    """If the list drifts, the skill teaches an agent to write rejected clauses."""
    for word in _default_vague_words():
        assert word in skill_text, word


def test_the_skill_requires_exactly_one_role_tag(skill_text):
    assert "@primary" in skill_text and "@counterexample" in skill_text
    assert "exactly one tag" in skill_text


def test_the_skill_states_the_thresholds_the_validator_enforces(skill_text, repo_config):
    lowered = skill_text.lower()
    assert "at least one `@primary`" in lowered
    assert "at least two `@counterexample`" in lowered
    # The words the skill uses must still be the numbers the validator enforces.
    assert (repo_config.min_primary, repo_config.min_counterexamples) == (1, 2)


def test_the_skill_covers_every_phase_the_design_names(skill_text):
    for phase in ("Phase 0", "Phase 1", "Phase 2", "Phase 3",
                  "Phase 4", "Phase 5", "Phase 6", "Phase 7", "Phase 8"):
        assert f"## {phase}" in skill_text, phase


def test_the_skill_only_uses_commands_that_exist(skill_text):
    import re
    from amigos.cli import build_parser
    known = set(build_parser()._subparsers._group_actions[0].choices)
    used = set(re.findall(r"^\s*amigos ([a-z]+)", skill_text, re.MULTILINE))
    assert used <= known, used - known
    assert {"create", "check", "state"} <= used


def test_every_state_the_skill_sets_is_declarable(skill_text):
    import re
    for declared in re.findall(r"amigos state \S+ --set (\S+)", skill_text):
        assert declared in story.DECLARABLE_STATES, declared


def test_the_skill_does_not_promise_a_check_the_validator_lacks(skill_text):
    import re
    named = set(re.findall(r"\b([a-z_]+_(?:defined|present|determinable|resolved))\b", skill_text))
    assert named <= set(dor.CHECK_NAMES), named - set(dor.CHECK_NAMES)
