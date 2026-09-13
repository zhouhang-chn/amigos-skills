"""STORY-007: the repository gate.

One test per acceptance scenario, named after it, plus the unit tests the
scenarios rest on.
"""

import json
import subprocess

import pytest

from amigos import config as config_module, gate
from amigos.cli import main

GOVERNED = "src/amigos/gate.py"


def cfg_for(root):
    return config_module.load(root=root)


# ---------------------------------------------------------------- scenarios

def test_a_governed_change_under_a_ready_story_is_permitted(git_repo):
    decision = gate.decide(cfg_for(git_repo), [GOVERNED], override="READY-001")
    assert decision.permitted is True
    assert decision.exit_code == gate.PERMITTED
    assert "READY-001" in decision.reason


def test_the_environment_overrides_the_branch_name(on_branch, monkeypatch):
    repo = on_branch("story/BLOCKED-001-something")
    monkeypatch.setenv("AMIGOS_STORY", "READY-001")
    story_id, source, problem = gate.resolve_story(cfg_for(repo))
    assert (story_id, source, problem) == ("READY-001", gate.SOURCE_ENV, None)


def test_a_governed_change_under_a_story_that_is_not_ready_is_refused(git_repo):
    decision = gate.decide(cfg_for(git_repo), [GOVERNED], override="BLOCKED-001")
    assert decision.permitted is False
    assert decision.exit_code == gate.REFUSED
    assert "BLOCKED-001" in decision.reason
    assert "blocking_questions_resolved" in decision.reason


def test_a_governed_change_with_no_resolvable_story_is_refused(git_repo):
    decision = gate.decide(cfg_for(git_repo), [GOVERNED])
    assert decision.permitted is False
    for place in gate.RESOLUTION_ORDER:
        assert place in decision.reason


def test_a_change_touching_only_exempt_paths_needs_no_story(git_repo):
    decision = gate.decide(
        cfg_for(git_repo), ["docs/README.md", ".amigos/stories/X/intent.md", "README.md"])
    assert decision.permitted is True
    assert decision.governed == []
    assert decision.story_id is None


def test_a_path_in_no_configured_directory_is_governed_anyway(git_repo):
    decision = gate.decide(
        cfg_for(git_repo), ["brand/new/directory/thing.py"], override="BLOCKED-001")
    assert decision.governed == ["brand/new/directory/thing.py"]
    assert decision.permitted is False


def test_a_branch_naming_two_stories_is_refused(on_branch):
    repo = on_branch("story/READY-001-and-BLOCKED-001")
    story_id, source, problem = gate.resolve_story(cfg_for(repo))
    assert story_id is None
    assert "READY-001" in problem and "BLOCKED-001" in problem
    decision = gate.decide(cfg_for(repo), [GOVERNED])
    assert decision.permitted is False


def test_a_stale_committed_verdict_does_not_permit_a_change(git_repo):
    """The gate recomputes: a dor.json the gated agent could write is inert."""
    directory = git_repo / ".amigos" / "stories" / "READY-001"
    assert main(["check", "--root", str(git_repo), "READY-001"]) == 0
    assert json.loads((directory / "dor.json").read_text())["ready"] is True

    feature = directory / "acceptance.feature"
    kept = feature.read_text().split("  @counterexample")[0]
    feature.write_text(kept)

    decision = gate.decide(cfg_for(git_repo), [GOVERNED], override="READY-001")
    assert decision.permitted is False
    assert "counterexamples_present" in decision.reason


def test_installing_the_git_hook_preserves_an_existing_one(git_repo, capsys):
    path = git_repo / ".git" / "hooks" / "pre-commit"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\necho someone elses hook\n")
    before = path.read_bytes()

    assert main(["hooks", "install", "--root", str(git_repo)]) == 2
    assert path.read_bytes() == before
    assert "refusing to overwrite" in capsys.readouterr().out


# ------------------------------------------------------------- unit support

@pytest.mark.parametrize("pattern,path,expected", [
    ("docs/**", "docs/a/b.md", True),
    ("docs/**", "./docs/a/b.md", True),
    ("docs/**", "docsx/a.md", False),
    ("*.md", "README.md", True),
    ("*.md", "src/notes.md", False),
    (".amigos/**", ".amigos/stories/S/intent.md", True),
    ("LICENSE", "LICENSE", True),
    ("LICENSE", "LICENSE.txt", False),
])
def test_glob_matching_respects_path_separators(pattern, path, expected):
    assert gate.is_exempt(path, (pattern,)) is expected


def test_governance_is_the_default_for_an_empty_exempt_set():
    assert gate.is_exempt("anything/at/all.py", ()) is False


@pytest.mark.parametrize("branch,expected", [
    ("story/STORY-007-repository-gate", ["STORY-007"]),
    ("STORY-007", ["STORY-007"]),
    ("feature/no-story-here", []),
    # The point is that STORY-007 must not match inside STORY-0071; the longer
    # id matching itself is correct.
    ("story/STORY-0071-other", ["STORY-0071"]),
    ("xSTORY-007", []),
])
def test_branch_matching_is_bounded_to_whole_story_ids(branch, expected):
    assert gate.stories_named_in(branch, ["STORY-007", "STORY-0071"]) == expected


def test_the_pointer_file_beats_the_branch_name(on_branch):
    repo = on_branch("story/BLOCKED-001-x")
    (repo / ".amigos" / gate.ACTIVE_FILE).write_text("\n\nREADY-001\n")
    story_id, source, _ = gate.resolve_story(cfg_for(repo))
    assert (story_id, source) == ("READY-001", gate.SOURCE_POINTER)


def test_the_branch_name_is_the_last_resort(on_branch):
    repo = on_branch("story/READY-001-x")
    story_id, source, _ = gate.resolve_story(cfg_for(repo))
    assert (story_id, source) == ("READY-001", gate.SOURCE_BRANCH)


def test_a_story_that_cannot_be_evaluated_refuses_rather_than_raising(git_repo):
    decision = gate.decide(cfg_for(git_repo), [GOVERNED], override="SELFPROMO-001")
    assert decision.permitted is False
    assert "not declarable" in decision.reason


def test_staged_paths_come_from_the_index(git_repo):
    target = git_repo / "src_new.py"
    target.write_text("x = 1\n")
    subprocess.run(["git", "add", "src_new.py"], cwd=git_repo, check=True)
    assert gate.staged_paths(git_repo) == ["src_new.py"]


def test_the_gate_refuses_when_git_cannot_report_changes(tmp_path):
    (tmp_path / ".amigos").mkdir()
    with pytest.raises(gate.GateUnavailable):
        gate.staged_paths(tmp_path)


# -------------------------------------------------------------------- cli

def test_cli_permits_and_reports(git_repo, capsys):
    code = main(["gate", "--root", str(git_repo), "--story", "READY-001",
                 "--changed-file", GOVERNED])
    assert code == gate.PERMITTED
    assert "permitted" in capsys.readouterr().out


def test_cli_refuses_on_stderr_with_guidance(git_repo, capsys):
    code = main(["gate", "--root", str(git_repo), "--changed-file", GOVERNED])
    assert code == gate.REFUSED
    captured = capsys.readouterr()
    assert "refused" in captured.err
    assert "AMIGOS_STORY" in captured.err
    assert captured.out == ""


def test_cli_json_output_carries_the_decision(git_repo, capsys):
    main(["gate", "--root", str(git_repo), "--story", "BLOCKED-001",
          "--changed-file", GOVERNED, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["permitted"] is False
    assert payload["governed"] == [GOVERNED]
    assert payload["state"] == "blocked"


def test_cli_rejects_contradictory_inputs(git_repo, capsys):
    code = main(["gate", "--root", str(git_repo), "--staged", "--changed-file", GOVERNED])
    assert code == 2
    assert "not both" in capsys.readouterr().err
