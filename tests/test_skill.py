"""STORY-004 and STORY-005: the discipline the skill states.

A prompt cannot be unit tested for behaviour, but it can be held to the rules it
is supposed to carry. These tests fail when the instructions drift away from what
the code enforces, which is the drift that matters: the skill telling an agent to
do something the validator forbids, or omitting a rule nothing else enforces.
"""

from pathlib import Path

import pytest

from amigos import dor, findings, story

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


def test_the_skill_forbids_carrying_one_role_into_another(skill_text):
    """v0.4: blind drafting is the milestone. Stated as a prohibition, not a hope."""
    assert "Put one role's work into another role's prompt during drafting" in skill_text


def test_the_skill_never_proposes_a_fork(skill_text):
    """A fork inherits this conversation, which by Phase 1 holds the other roles' work.

    Every mention of forking must be a prohibition. A single sentence that lost
    its 'never' would silently turn blind drafting back into shared context.
    """
    mentions = [line for line in skill_text.splitlines() if "fork" in line.lower()]
    assert mentions, "the skill must say something about forks"
    for line in mentions:
        assert "never" in line.lower() or "not" in line.lower(), line


def test_the_skill_spawns_each_role_by_its_agent_type(skill_text):
    for role in findings.ROLES:
        assert f"`{role}`" in skill_text, role


def test_the_skill_stops_when_a_role_returns_nothing(skill_text):
    """STORY-005: two roles plus a gap is not the Three Amigos."""
    assert "the run stops here" in skill_text
    assert "a contract reconciled from" in skill_text


def test_the_skill_covers_every_phase_the_design_names(skill_text):
    for phase in ("Phase 0", "Phase 1", "Phase 2", "Phase 3",
                  "Phase 4", "Phase 5", "Phase 6", "Phase 7"):
        assert f"## {phase}" in skill_text, phase
    assert "## Phase 8" not in skill_text, "v0.4 folded the challenge phase into Phase 3"


def test_the_skill_only_uses_commands_that_exist(skill_text):
    import re
    from amigos.cli import build_parser
    known = set(build_parser()._subparsers._group_actions[0].choices)
    used = set(re.findall(r"^\s*amigos ([a-z]+)", skill_text, re.MULTILINE))
    assert used <= known, used - known
    assert {"create", "check", "state", "findings"} <= used


def test_every_state_the_skill_sets_is_declarable(skill_text):
    import re
    for declared in re.findall(r"amigos state \S+ --set (\S+)", skill_text):
        assert declared in story.DECLARABLE_STATES, declared


def test_the_skill_does_not_promise_a_check_the_validator_lacks(skill_text):
    import re
    named = set(re.findall(r"\b([a-z_]+_(?:defined|present|determinable|resolved))\b", skill_text))
    assert named <= set(dor.CHECK_NAMES), named - set(dor.CHECK_NAMES)
