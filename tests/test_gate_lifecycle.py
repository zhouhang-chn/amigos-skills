"""STORY-011: a contract state change leaves evidence, and a blocked story permits no work.

One test per acceptance scenario, named after it.

The rule is *not* that ``state.json`` must not move — it is supposed to move, and
a story mid-drafting has uncommitted transitions by design. The rule is that the
record must hold together: ``declared_state`` and ``updated_at`` must be the ones
the last history entry records, and the committed history must still be a prefix
of the working tree's.

The refusal is a gate decision and never a readiness verdict. Routing it through
readiness would invert it: ``gate.frozen_contracts()`` freezes only a story that
demonstrably evaluates ready, so a tampered story reported as *not ready* would
have its contract released rather than held.
"""

import json
import subprocess

from amigos import config as config_module, gate, story
from amigos.cli import main

READY = "READY-001"
BLOCKED = "BLOCKED-001"
FEATURE = f".amigos/stories/{READY}/acceptance.feature"
STATE = f".amigos/stories/{READY}/state.json"
SOURCE = "src/amigos/gate.py"

T0 = "2026-01-01T00:00:00Z"
T1 = "2026-01-02T00:00:00Z"
T2 = "2026-01-03T00:00:00Z"


def cfg_for(root):
    return config_module.load(root=root)


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=True)


def entry(state, at, note="recorded"):
    return {"state": state, "at": at, "note": note}


def tamper_declaration(directory, declared):
    """Hand-set ``declared_state``, leaving the recorded history untouched.

    This is the edit the story exists to catch: the record still has every entry
    it was committed with, and the declaration is simply one none of them made.
    """
    path = directory / "state.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["declared_state"] = declared
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_state(directory, declared, history, updated_at=None):
    """Write a lifecycle record directly, the way a text editor would."""
    payload = {
        "schema_version": 1,
        "story_id": directory.name,
        "declared_state": declared,
        "updated_at": updated_at if updated_at is not None else history[-1]["at"],
        "history": history,
    }
    (directory / "state.json").write_text(json.dumps(payload, indent=2) + "\n",
                                          encoding="utf-8")


def three_committed(root, story_id=READY):
    """A story whose committed state.json records three history entries."""
    cfg = cfg_for(root)
    directory = cfg.story_dir(story_id)
    history = [entry("draft", T0), entry("amigos_running", T1),
               entry("contract_change", T2)]
    write_state(directory, "contract_change", history)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "three transitions")
    return cfg, directory, history


# ---------------------------------------------------------------- scenarios

def test_a_declared_state_the_history_does_not_record_is_refused(git_repo):
    cfg = cfg_for(git_repo)
    directory = cfg.story_dir(READY)
    tamper_declaration(directory, "contract_change")

    decision = gate.decide(cfg, [FEATURE])

    assert decision.permitted is False
    assert decision.exit_code == gate.REFUSED
    assert READY in decision.reason
    assert "state.json" in decision.reason
    assert "contract_change" in decision.reason
    assert "does not record" in decision.reason


def test_that_refusal_does_not_tell_the_caller_to_make_the_story_ready(git_repo, capsys):
    """The last Then of the same scenario, judged at the surface a human reads."""
    cfg = cfg_for(git_repo)
    tamper_declaration(cfg.story_dir(READY), "contract_change")

    code = main(["gate", "--root", str(git_repo), "--changed-file", FEATURE])

    captured = capsys.readouterr()
    assert code == gate.REFUSED
    assert "Make the story ready" not in captured.err
    assert "state.json" in captured.err


def test_a_history_entry_removed_after_it_was_committed_is_refused(git_repo):
    cfg, directory, history = three_committed(git_repo)
    write_state(directory, "amigos_running", history[:2])

    decision = gate.decide(cfg, [SOURCE], override=READY)

    assert decision.permitted is False
    assert decision.exit_code == gate.REFUSED
    assert "state.json" in decision.reason
    assert "contract_change" in decision.reason, (
        "the refusal names the state of the removed entry"
    )


def test_a_governed_change_under_a_blocked_story_is_refused_with_the_route_out(
        git_repo, capsys):
    edit = main(["gate", "--root", str(git_repo), "--story", BLOCKED,
                 "--changed-file", SOURCE])
    edit_err = capsys.readouterr().err

    _git(git_repo, "commit", "-q", "--allow-empty", "-m", "empty")
    (git_repo / SOURCE).parent.mkdir(parents=True, exist_ok=True)
    (git_repo / SOURCE).write_text("# changed\n", encoding="utf-8")
    _git(git_repo, "add", SOURCE)
    staged = main(["gate", "--root", str(git_repo), "--story", BLOCKED, "--staged"])
    staged_err = capsys.readouterr().err

    assert edit == gate.REFUSED and staged == gate.REFUSED
    for err in (edit_err, staged_err):
        assert "blocked" in err
        assert any(name in err for name in (
            "intent_defined", "scope_defined", "constraints_defined",
            "primary_scenario_present", "counterexamples_present",
            "assertions_are_determinable", "blocking_questions_resolved",
        )), "the refusal names a failed Definition of Ready check by its check name"
        assert "amigos skill" in err


def test_a_reopening_recorded_through_the_state_command_is_permitted(git_repo):
    cfg = cfg_for(git_repo)
    directory = cfg.story_dir(READY)
    story.set_state(directory, "contract_change", note="a genuine conflict")
    written = (directory / "state.json").read_bytes()

    assert gate.decide(cfg, [FEATURE]).permitted is True
    assert main(["state", "--root", str(git_repo), READY]) == 0
    assert (directory / "state.json").read_bytes() == written


def test_declaring_contract_change_still_reopens_a_frozen_contract(git_repo):
    """STORY-010's rule, held against this story's change."""
    cfg = cfg_for(git_repo)
    assert gate.decide(cfg, [FEATURE]).permitted is False

    assert gate.decide(cfg, [STATE]).permitted is True, (
        "the write that declares contract_change must itself be permitted"
    )
    story.set_state(cfg.story_dir(READY), "contract_change", note="a genuine conflict")

    assert gate.decide(cfg, [FEATURE]).exit_code == gate.PERMITTED


def test_the_commit_that_would_launder_a_rewritten_history_is_refused(git_repo):
    cfg, directory, history = three_committed(git_repo)
    write_state(directory, "amigos_running", history[:2])
    _git(git_repo, "add", STATE)

    paths = gate.staged_paths(git_repo)
    decision = gate.decide(cfg, paths, override=READY, staged=True)

    assert decision.permitted is False
    assert "state.json" in decision.reason


def test_a_write_to_the_storys_own_state_json_is_permitted_while_inconsistent(git_repo):
    cfg = cfg_for(git_repo)
    tamper_declaration(cfg.story_dir(READY), "contract_change")

    assert gate.decide(cfg, [STATE]).exit_code == gate.PERMITTED, (
        "a record the gate rejects must stay repairable"
    )
    assert gate.decide(cfg, [FEATURE]).exit_code == gate.REFUSED


def test_a_state_json_that_cannot_be_parsed_is_refused_rather_than_permitted(git_repo):
    cfg = cfg_for(git_repo)
    (cfg.story_dir(READY) / "state.json").write_text("{ not json", encoding="utf-8")

    decision = gate.decide(cfg, [FEATURE])

    assert decision.permitted is False
    assert "state.json" in decision.reason


def test_a_state_json_that_was_never_committed_is_not_reported_as_inconsistent(git_repo):
    cfg = cfg_for(git_repo)
    story.create(cfg, "FRESH-001", templates_dir=git_repo / "templates")

    decision = gate.decide(cfg, [SOURCE], override="FRESH-001")

    assert "state.json" not in decision.reason
    assert main(["state", "--root", str(git_repo), "FRESH-001"]) == 2


def test_no_declarable_state_makes_a_blocked_story_permit_a_governed_change(git_repo):
    cfg = cfg_for(git_repo)
    directory = cfg.story_dir(BLOCKED)

    for declared in story.DECLARABLE_STATES:
        story.set_state(directory, declared, note="in turn")
        decision = gate.decide(cfg, [SOURCE], override=BLOCKED)

        assert decision.exit_code == gate.REFUSED, declared
        assert decision.state != "ready", declared


def test_every_story_in_this_repository_passes_the_consistency_rule(repo_config, capsys):
    directories = sorted(d for d in repo_config.stories_dir.iterdir() if d.is_dir())
    assert directories, "this repository has stories"

    for directory in directories:
        code = main(["state", "--root", str(repo_config.root), directory.name])
        out = capsys.readouterr().out

        assert code == 0, f"{directory.name}: {out}"
        assert "does not record" not in out


def test_the_report_writes_nothing(git_repo, capsys):
    cfg = cfg_for(git_repo)
    directory = cfg.story_dir(READY)
    tamper_declaration(directory, "contract_change")
    before = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}

    code = main(["state", "--root", str(git_repo), READY])
    capsys.readouterr()

    assert code == 1
    after = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    assert after == before
