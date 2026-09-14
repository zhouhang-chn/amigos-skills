"""STORY-010: the gate refuses a contract edit while a story is ready.

One test per acceptance scenario, named after it.

Readiness for this decision is derived from the contract *before* the change:
the working tree when an edit is being attempted, ``HEAD`` when a staged set is
being committed. Deriving it from the edited content would permit the most
damaging edits and refuse only the harmless ones, because deleting a
counterexample is itself an edit that leaves a story unready.

The rule fails open, which is the opposite of the gate's default: a path is
refused only when the story that owns it demonstrably evaluates ready. A
contract that cannot be evaluated must stay editable, or it could never be
repaired.
"""

import shutil
import subprocess

from amigos import config as config_module, dor, gate, story
from amigos.cli import main

READY = "READY-001"
FEATURE = f".amigos/stories/{READY}/acceptance.feature"


def cfg_for(root):
    return config_module.load(root=root)


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=True)


# ---------------------------------------------------------------- scenarios

def test_an_edit_to_a_ready_storys_acceptance_criteria_is_refused(git_repo):
    decision = gate.decide(cfg_for(git_repo), [FEATURE])

    assert decision.permitted is False
    assert decision.exit_code == gate.REFUSED
    assert "acceptance.feature" in decision.reason
    assert READY in decision.reason
    assert "contract_change" in decision.reason


def test_the_refusal_does_not_tell_the_caller_to_make_the_story_ready(git_repo, capsys):
    """The last Then of the same scenario, judged at the surface a human reads."""
    code = main(["gate", "--root", str(git_repo), "--changed-file", FEATURE])

    captured = capsys.readouterr()
    assert code == gate.REFUSED
    assert "Make the story ready" not in captured.err
    assert "contract_change" in captured.err
    assert READY in captured.err


def test_declaring_a_withholding_state_reopens_the_contract(git_repo):
    cfg = cfg_for(git_repo)
    assert gate.decide(cfg, [FEATURE]).permitted is False

    state_path = f".amigos/stories/{READY}/state.json"
    assert gate.decide(cfg, [state_path]).permitted is True, (
        "the write that declares contract_change must itself be permitted"
    )
    story.set_state(cfg.story_dir(READY), "contract_change", note="reopen")

    decision = gate.decide(cfg, [FEATURE])

    assert decision.permitted is True
    assert decision.exit_code == gate.PERMITTED


def test_an_edit_that_would_leave_the_story_unready_is_refused_all_the_same(committed_repo):
    cfg = cfg_for(committed_repo)
    feature = cfg.story_dir(READY) / "acceptance.feature"
    kept, _, _ = feature.read_text().rpartition("  @counterexample")
    feature.write_text(kept.rstrip() + "\n")
    _git(committed_repo, "add", "-A")

    assert dor.evaluate(cfg, READY).ready is False, (
        "the edited contract is unready, so a tree-derived rule would permit it"
    )

    decision = gate.decide(cfg, gate.staged_paths(committed_repo), staged=True)

    assert decision.permitted is False
    assert decision.exit_code == gate.REFUSED
    assert "acceptance.feature" in decision.reason
    assert "counterexamples_present" not in decision.reason


def test_the_commit_that_first_records_a_ready_contract_is_permitted(committed_repo):
    cfg = cfg_for(committed_repo)
    fresh = "FRESH-001"
    directory = story.create(cfg, fresh)
    for name in story.HASHED_FILES:
        shutil.copy(cfg.story_dir(READY) / name, directory / name)
    dor.write(dor.evaluate(cfg, fresh))
    assert dor.evaluate(cfg, fresh).ready is True
    _git(committed_repo, "add", "-A")

    decision = gate.decide(cfg, gate.staged_paths(committed_repo), staged=True)

    assert decision.permitted is True
    assert decision.exit_code == gate.PERMITTED


def test_a_story_that_is_not_ready_keeps_an_editable_contract(git_repo):
    cfg = cfg_for(git_repo)
    for name in story.HASHED_FILES:
        decision = gate.decide(cfg, [f".amigos/stories/BLOCKED-001/{name}"])
        assert decision.permitted is True, name
        assert decision.exit_code == gate.PERMITTED


def test_only_the_contract_inputs_are_frozen_not_the_records_beside_them(git_repo):
    cfg = cfg_for(git_repo)
    base = f".amigos/stories/{READY}"
    beside = (
        f"{base}/dor.json",
        f"{base}/state.json",
        f".amigos/runs/{READY}/2026-01-01T00-00-00Z/implementation.md",
    )
    for path in beside:
        assert gate.decide(cfg, [path]).permitted is True, path

    assert gate.decide(cfg, [f"{base}/acceptance.feature"]).permitted is False


def test_the_refusal_follows_the_story_the_path_names_not_the_active_one(on_branch):
    repo = on_branch(f"story/{READY}-active")
    cfg = cfg_for(repo)
    second = "READY-002"
    shutil.copytree(cfg.story_dir(READY), cfg.story_dir(second))

    resolved, _, _ = gate.resolve_story(cfg)
    assert resolved == READY, "the active story is the one the branch names"

    decision = gate.decide(cfg, [f".amigos/stories/{second}/acceptance.feature"])

    assert decision.permitted is False
    assert second in decision.reason


def test_a_story_whose_contract_cannot_be_evaluated_stays_editable(git_repo):
    cfg = cfg_for(git_repo)
    unevaluable = (
        ".amigos/stories/BADGHERKIN-001/acceptance.feature",
        ".amigos/stories/NOSUCHSTORY-001/acceptance.feature",
    )
    for path in unevaluable:
        decision = gate.decide(cfg, [path])
        assert decision.permitted is True, path
        assert decision.exit_code == gate.PERMITTED


def test_a_staged_deletion_of_a_ready_storys_contract_file_is_refused(committed_repo):
    _git(committed_repo, "rm", "-q", FEATURE)

    staged = gate.staged_paths(committed_repo)
    assert FEATURE in staged, "a staged deletion must reach a decision at all"

    decision = gate.decide(cfg_for(committed_repo), staged, staged=True)

    assert decision.permitted is False
    assert decision.exit_code == gate.REFUSED
    assert "acceptance.feature" in decision.reason


def test_scaffolding_a_new_story_is_permitted_while_another_story_is_ready(git_repo):
    cfg = cfg_for(git_repo)
    assert dor.evaluate(cfg, READY).ready is True
    story.create(cfg, "SCAFFOLD-001")
    paths = [f".amigos/stories/SCAFFOLD-001/{name}" for name in story.INPUT_FILES]

    decision = gate.decide(cfg, paths)

    assert decision.permitted is True
    assert decision.exit_code == gate.PERMITTED
