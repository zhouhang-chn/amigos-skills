"""STORY-005: the three drafting agents, held to what the code enforces.

A prompt cannot be tested for what a model does with it. It can be tested for
naming a file that exists, a threshold the validator agrees with, and a
vocabulary the linter has not moved away from. Those are the drifts that would
otherwise go unnoticed: the agent keeps working, the contract keeps passing, and
the instructions quietly stop describing the system.
"""

import json
import re
from pathlib import Path

import pytest

from amigos import findings, jsonschema
from amigos.config import _default_vague_words

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS = REPO_ROOT / "agents"


@pytest.fixture(scope="module")
def agent_text() -> dict[str, str]:
    return {role: (AGENTS / f"{role}.md").read_text(encoding="utf-8")
            for role in findings.ROLES}


def _section(text: str, heading: str) -> str:
    """Return one `## heading` section, up to the next heading of any level."""
    start = text.index(f"## {heading}")
    rest = text[start:]
    match = re.search(r"\n#{1,6} ", rest[3:])
    return rest if match is None else rest[:match.start() + 3]


def test_there_is_one_agent_file_per_role():
    assert sorted(p.name for p in AGENTS.glob("*.md")) == \
           sorted(f"{role}.md" for role in findings.ROLES)


def test_the_plugin_declares_the_agents_directory():
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["agents"] == "./agents"


@pytest.mark.parametrize("role", findings.ROLES)
def test_this_checkout_discovers_the_same_file_the_plugin_ships(role):
    link = REPO_ROOT / ".claude" / "agents" / f"{role}.md"
    assert link.is_symlink(), "the checkout should not hold a second copy"
    assert link.resolve() == (AGENTS / f"{role}.md").resolve()


@pytest.mark.parametrize("role", findings.ROLES)
def test_each_agent_declares_its_own_name(agent_text, role):
    text = agent_text[role]
    assert text.startswith("---\n")
    front = text.split("---", 2)[1]
    assert f"name: {role}" in front
    assert "description:" in front


def test_all_three_roles_share_one_risk_vocabulary(agent_text):
    """The count of findings only one role made is only as honest as this list.

    If each role reached for its own words, two roles noticing the same risk
    would be counted as two findings and the split would look valuable because
    of vocabulary rather than perspective.
    """
    sections = {role: _section(text, "Risk dimensions")
                for role, text in agent_text.items()}
    assert len(set(sections.values())) == 1, "the risk dimension sections have drifted"


def test_the_shared_vocabulary_is_a_suggestion_and_says_so(agent_text):
    """STORY-005 defers a *fixed* vocabulary; this list is offered, not enforced."""
    section = _section(agent_text["product"], "Risk dimensions")
    assert "Coin a new one only if none of them does" in section
    assert jsonschema.load_schema(findings.RECORD_SCHEMA)[
        "properties"]["findings"]["items"]["properties"]["risk_dimension"] == \
        {"type": "string", "minLength": 1}


@pytest.mark.parametrize("role", findings.ROLES)
def test_each_agent_emits_a_record_the_schema_accepts(agent_text, role):
    """The example each agent is shown must be one `amigos findings` would take."""
    text = agent_text[role]
    block = next(b for b in re.findall(r"```json\n(.*?)```", text, re.DOTALL)
                 if '"findings"' in b)
    payload = json.loads(block.replace("<the story id from your prompt>", "STORY-001"))
    schema = jsonschema.load_schema(findings.RECORD_SCHEMA)
    assert jsonschema.validate(payload, schema) == []
    assert payload["role"] == role


@pytest.mark.parametrize("role", findings.ROLES)
def test_no_agent_may_write_into_a_story(agent_text, role):
    assert "`.amigos/stories/`" in agent_text[role]
    assert "must not" in agent_text[role].lower()


@pytest.mark.parametrize("role", findings.ROLES)
def test_no_agent_interviews_the_user(agent_text, role):
    """The interview is bounded at two rounds; three agents asking is not bounded."""
    assert "Ask the user a question" in agent_text[role]


@pytest.mark.parametrize("role", findings.ROLES)
def test_every_agent_is_told_it_cannot_see_the_others(agent_text, role):
    assert "will not see the other two roles' work" in agent_text[role]


@pytest.mark.parametrize("role", findings.ROLES)
def test_no_agent_is_given_a_tool_that_writes_to_the_repository(agent_text, role):
    """Read-only plus Write, so the prohibitions are not the only thing holding.

    Without Bash an agent cannot run `amigos state`, `amigos check` or git, none
    of which belong to a drafting role.
    """
    front = agent_text[role].split("---", 2)[1]
    tools = {t.strip() for t in re.search(r"tools: (.+)", front).group(1).split(",")}
    assert tools == {"Read", "Grep", "Glob", "Write"}


def test_the_qa_agent_names_every_vague_word_the_linter_rejects(agent_text):
    """QA writes the assertions, so QA is where the list has to be right."""
    for word in _default_vague_words():
        assert word in agent_text["qa"], word


def test_the_qa_agent_states_the_thresholds_the_validator_enforces(agent_text, repo_config):
    lowered = agent_text["qa"].lower()
    assert "at least one `@primary`" in lowered
    assert "at least two `@counterexample`" in lowered
    assert (repo_config.min_primary, repo_config.min_counterexamples) == (1, 2)


def test_the_qa_agent_requires_exactly_one_role_tag(agent_text):
    assert "exactly one tag" in agent_text["qa"]


def test_each_agent_drafts_the_file_the_validator_reads(agent_text):
    """A role drafting a file nothing reads would pass every other test here."""
    from amigos import story
    drafted = {"product": "intent.md", "dev": "constraints.md", "qa": "acceptance.feature"}
    for role, filename in drafted.items():
        assert filename in story.HASHED_FILES
        assert f"`{filename}`" in agent_text[role]
