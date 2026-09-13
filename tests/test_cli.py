import json
import subprocess
import sys
from pathlib import Path

import pytest

from amigos import dor
from amigos.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = str(REPO_ROOT / "tests" / "fixtures" / "stories")


def check(story_id, *extra):
    return main(["check", "--stories-dir", FIXTURES, "--no-write", story_id, *extra])


@pytest.mark.parametrize("story_id,expected", [
    ("READY-001", dor.EXIT_READY),
    ("VAGUE-001", dor.EXIT_NOT_READY),
    ("BLOCKED-001", dor.EXIT_NOT_READY),
    ("ONECOUNTER-001", dor.EXIT_NOT_READY),
    ("PLACEHOLDER-001", dor.EXIT_NOT_READY),
    ("NOTHEN-001", dor.EXIT_NOT_READY),
    ("RUNNING-001", dor.EXIT_NOT_READY),
    ("UNTAGGED-001", dor.EXIT_STRUCTURAL),
    ("SELFPROMO-001", dor.EXIT_STRUCTURAL),
    ("MISSING-001", dor.EXIT_STRUCTURAL),
    ("BADGHERKIN-001", dor.EXIT_STRUCTURAL),
])
def test_exit_codes_separate_not_ready_from_malformed(story_id, expected):
    assert check(story_id) == expected


def test_report_marks_each_check(capsys):
    check("READY-001")
    out = capsys.readouterr().out
    assert out.count("[PASS]") == 7
    assert "ready: true" in out


def test_report_names_the_failing_check(capsys):
    check("BLOCKED-001")
    out = capsys.readouterr().out
    assert "[FAIL] blocking_questions_resolved" in out
    assert "ready: false" in out


def test_report_explains_a_withheld_state(capsys):
    check("RUNNING-001")
    assert "state.json declares amigos_running" in capsys.readouterr().out


def test_json_output_is_the_dor_payload(capsys):
    check("READY-001", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["ready"] is True
    assert tuple(payload["checks"]) == dor.CHECK_NAMES


def test_structural_defect_reports_to_stderr(capsys):
    assert check("MISSING-001") == dor.EXIT_STRUCTURAL
    captured = capsys.readouterr()
    assert "constraints.md" in captured.err
    assert captured.out == ""


def test_check_writes_dor_by_default(scratch_repo):
    assert main(["check", "--root", str(scratch_repo), "READY-001"]) == dor.EXIT_READY
    written = scratch_repo / ".amigos" / "stories" / "READY-001" / "dor.json"
    assert json.loads(written.read_text())["state"] == "ready"


def test_no_write_leaves_the_directory_untouched(scratch_repo):
    main(["check", "--root", str(scratch_repo), "--no-write", "READY-001"])
    assert not (scratch_repo / ".amigos" / "stories" / "READY-001" / "dor.json").exists()


def test_lint_exits_clean_on_a_judgeable_contract():
    assert main(["lint", "--stories-dir", FIXTURES, "READY-001"]) == 0


def test_lint_reports_findings_and_exits_one(capsys):
    assert main(["lint", "--stories-dir", FIXTURES, "VAGUE-001"]) == 1
    out = capsys.readouterr().out
    assert "vague-assertion" in out
    assert "acceptance.feature:13" in out


def test_lint_untagged_scenario_exits_one(capsys):
    assert main(["lint", "--stories-dir", FIXTURES, "UNTAGGED-001"]) == 1
    assert "untagged-scenario" in capsys.readouterr().out


def test_lint_accepts_a_file_directly(capsys):
    path = REPO_ROOT / "tests" / "fixtures" / "stories" / "VAGUE-001" / "acceptance.feature"
    assert main(["lint", "--file", str(path)]) == 1


def test_lint_json_output_carries_rule_and_line(capsys):
    main(["lint", "--stories-dir", FIXTURES, "VAGUE-001", "--json"])
    findings = json.loads(capsys.readouterr().out)
    assert findings[0]["rule"] == "vague-assertion"
    assert findings[0]["line"] == 13


def test_init_creates_a_config_and_leaves_an_existing_one(tmp_path, capsys):
    assert main(["init", "--root", str(tmp_path)]) == 0
    config_path = tmp_path / ".amigos" / "config.json"
    assert json.loads(config_path.read_text())["stories_dir"] == ".amigos/stories"
    config_path.write_text('{"stories_dir": "custom"}')
    assert main(["init", "--root", str(tmp_path)]) == 0
    assert json.loads(config_path.read_text())["stories_dir"] == "custom"


def test_a_freshly_scaffolded_story_is_not_ready(scratch_repo, capsys):
    assert main(["create", "--root", str(scratch_repo), "STORY-999"]) == 0
    assert main(["check", "--root", str(scratch_repo), "STORY-999"]) == dor.EXIT_NOT_READY
    out = capsys.readouterr().out
    assert "[FAIL] intent_defined" in out


def test_status_lists_every_story(scratch_repo, capsys):
    # The scratch corpus holds structurally broken stories too, and the worst
    # outcome in the repository is the one status reports.
    code = main(["status", "--root", str(scratch_repo)])
    out = capsys.readouterr().out
    assert "READY-001" in out and "ready" in out
    assert "BLOCKED-001" in out and "blocked" in out
    assert "MISSING-001" in out and "error" in out
    assert code == dor.EXIT_STRUCTURAL


def test_status_reports_not_ready_when_nothing_is_malformed(scratch_repo, capsys):
    import shutil
    stories = scratch_repo / ".amigos" / "stories"
    for broken in ("MISSING-001", "SELFPROMO-001", "UNTAGGED-001", "BADGHERKIN-001"):
        shutil.rmtree(stories / broken)
    assert main(["status", "--root", str(scratch_repo)]) == dor.EXIT_NOT_READY


def test_status_is_clean_when_every_story_is_ready(scratch_repo):
    import shutil
    stories = scratch_repo / ".amigos" / "stories"
    for directory in list(stories.iterdir()):
        if directory.name != "READY-001":
            shutil.rmtree(directory)
    assert main(["status", "--root", str(scratch_repo)]) == dor.EXIT_READY


def test_script_wrapper_matches_the_subcommand():
    script = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "check_dor.py"),
         "--stories-dir", FIXTURES, "--no-write", "VAGUE-001"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert script.returncode == dor.EXIT_NOT_READY
    assert "[FAIL] assertions_are_determinable" in script.stdout


# --- STORY-006: verify -------------------------------------------------------

def test_verify_is_registered():
    from amigos.cli import build_parser
    args = build_parser().parse_args(["verify", "STORY-006"])
    assert args.command == "verify"
    assert args.story_id == "STORY-006"


def test_verify_exits_zero_on_an_unchanged_ready_contract(committed_repo):
    from amigos import verify

    code = main(["verify", "--root", str(committed_repo), "READY-001"])
    assert code == verify.EXIT_OK


def test_verify_exits_one_and_names_the_changed_file(committed_repo, capsys):
    from amigos import verify
    feature = committed_repo / ".amigos" / "stories" / "READY-001" / "acceptance.feature"
    feature.write_text(feature.read_text() + "\n# moved\n")

    code = main(["verify", "--root", str(committed_repo), "READY-001"])
    out = capsys.readouterr().out

    assert code == verify.EXIT_NOT_VERIFIED
    assert "acceptance.feature" in out
    assert "verified: false" in out


def test_verify_exits_two_without_a_baseline(scratch_repo, capsys):
    """No git, so no committed contract: unanswerable, not refused."""
    code = main(["verify", "--root", str(scratch_repo), "READY-001"])
    assert code == 2
    assert capsys.readouterr().err.strip()


def test_verify_json_carries_the_per_file_verdict(committed_repo, capsys):
    main(["verify", "--root", str(committed_repo), "--json", "READY-001"])
    payload = json.loads(capsys.readouterr().out)

    assert payload["verified"] is True
    assert payload["contract"]["intent.md"] == "match"
