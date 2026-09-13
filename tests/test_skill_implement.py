"""STORY-006: the discipline the implement skill states.

A prompt cannot be unit tested for behaviour. It can be held to the rules the
code enforces and to the bounds nothing else enforces, which is the drift that
matters: the skill telling an agent to do something the validator forbids, or
dropping a rule that exists only here.

Several of STORY-006's scenarios describe agent behaviour no test in this
repository can observe. They are judged here as instructions present in the
prompt, and `docs/versions/v0.5-implement/implementation-notes.md` records that
substitution rather than counting them as test-decided.
"""

import json
from pathlib import Path

import pytest

from amigos import story, verify
from amigos.cli import build_parser

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "implement" / "SKILL.md"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def flowed(skill_text) -> str:
    """The skill with line wrapping removed, for phrases that span a line break.

    The assertion is that the skill says a thing, never that it says it on one
    line; reflowing the prose to satisfy a test would be the test dictating the
    document's shape.
    """
    return " ".join(skill_text.lower().split())


# --- packaging ---------------------------------------------------------------

def test_the_skill_ships_where_the_plugin_declares_it():
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["skills"] == "./skills"
    assert SKILL.is_file()


def test_this_checkout_discovers_the_same_file_the_plugin_ships():
    link = REPO_ROOT / ".claude" / "skills" / "implement"
    assert link.is_symlink(), "the checkout should not hold a second copy"
    assert (link / "SKILL.md").resolve() == SKILL.resolve()


def test_the_skill_declares_frontmatter(skill_text):
    assert skill_text.startswith("---\n")
    front = skill_text.split("---", 2)[1]
    assert "name: implement" in front
    assert "description:" in front


# --- every command it names must exist ---------------------------------------

def _subcommands() -> set[str]:
    actions = [a for a in build_parser()._actions if hasattr(a, "choices") and a.choices]
    for action in actions:
        if action.dest == "command":
            return set(action.choices)
    raise AssertionError("no subcommand action on the parser")


@pytest.mark.parametrize("command", ["check", "verify", "state", "status", "gate"])
def test_each_command_the_skill_names_exists(skill_text, command):
    assert f"amigos {command}" in skill_text
    assert command in _subcommands()


def test_the_only_state_it_declares_is_declarable(skill_text):
    assert "--set contract_change" in skill_text
    assert "contract_change" in story.DECLARABLE_STATES


# --- the prohibitions --------------------------------------------------------

def test_the_skill_forbids_editing_the_contract(skill_text):
    assert "Edit `intent.md`, `constraints.md`, `acceptance.feature`" in skill_text
    for name in story.HASHED_FILES:
        assert name in skill_text


def test_the_skill_forbids_writing_the_derived_verdict(skill_text):
    assert "Write or edit `dor.json`" in skill_text


def test_the_skill_forbids_declaring_readiness(skill_text):
    assert "Declare `ready` or `blocked` in `state.json`" in skill_text


def test_the_skill_forbids_trusting_the_recorded_verdict(skill_text):
    assert "Take a `ready: true` out of `dor.json` as authority" in skill_text
    assert "never read the verdict out of `dor.json`" in skill_text


def test_the_skill_forbids_hiding_a_failing_test(skill_text):
    assert "Delete, skip or `xfail` a test derived from a `Then` clause" in skill_text


def test_the_skill_forbids_a_privileged_path_around_the_gate(skill_text):
    assert "uninstall the pre-commit hook" in skill_text
    assert "commit with it skipped" in skill_text
    assert "Do not route around it." in skill_text


# --- the bounds nothing else enforces ----------------------------------------

def test_the_skill_requires_red_before_green(flowed):
    assert "against the unchanged source before writing any implementation" in flowed
    assert "proves nothing about intent" in flowed


def test_the_skill_requires_unobservable_clauses_to_be_named(flowed):
    assert "exclude them from the count of scenarios decided by tests" in flowed
    assert "name them and say what judges them instead" in flowed


def test_the_skill_reports_scope_expansion_without_stopping(flowed):
    assert "scope expansion" in flowed
    assert "do not stop the run" in flowed


def test_the_skill_stops_on_a_contract_conflict_without_re_contracting(skill_text):
    assert "Do not invoke the amigos skill yourself." in skill_text
    assert "must not both discover a conflict" in skill_text


def test_the_skill_declares_contract_change_last(skill_text, flowed):
    conflict = skill_text.split("If implementation proves the contract wrong")[1]
    report_at = conflict.index("Report the conflict")
    declare_at = conflict.index("--set contract_change")
    assert report_at < declare_at, "the report must exist before readiness is withheld"
    assert "declare `contract_change` **last**, after the report exists" in flowed
    assert "it withholds readiness the moment it is declared" in flowed


def test_the_skill_keeps_the_run_record_out_of_the_story_directory(skill_text, flowed):
    assert ".amigos/runs/<STORY-ID>/" in skill_text
    assert "never inside the story directory" in flowed


def test_the_skill_warns_against_rewriting_the_baseline(skill_text, flowed):
    assert "rewrites the baseline" in flowed
    assert "amigos verify" in skill_text


def test_the_verdict_the_skill_reports_is_the_one_verify_computes(skill_text):
    assert "verified: true" in skill_text
    assert "verified" in verify.Result.__dict__ or hasattr(verify.Result, "verified")
