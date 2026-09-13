import json

import pytest

from amigos import config as config_module, dor, jsonschema, story


def evaluate(cfg, story_id):
    return dor.evaluate(cfg, story_id)


def test_a_complete_contract_is_ready(fixture_config):
    result = evaluate(fixture_config, "READY-001")
    assert result.ready is True
    assert result.state == "ready"
    assert result.exit_code == dor.EXIT_READY
    assert all(result.checks.values())
    assert result.failures == []


def test_check_names_match_the_published_set(fixture_config):
    result = evaluate(fixture_config, "READY-001")
    assert tuple(result.checks) == dor.CHECK_NAMES
    assert len(dor.CHECK_NAMES) == 7


def test_a_blocking_question_withholds_readiness(fixture_config):
    result = evaluate(fixture_config, "BLOCKED-001")
    assert result.ready is False
    assert result.state == "blocked"
    assert result.checks["blocking_questions_resolved"] is False
    assert result.blocking_questions == ["Which identity provider authorises the caller?"]


def test_a_vague_assertion_withholds_readiness_and_cites_the_line(fixture_config):
    result = evaluate(fixture_config, "VAGUE-001")
    assert result.checks["assertions_are_determinable"] is False
    failure = next(f for f in result.failures if f.rule == "vague-assertion")
    assert failure.file.endswith("acceptance.feature")
    assert failure.line == 13


def test_one_counterexample_is_not_enough(fixture_config):
    result = evaluate(fixture_config, "ONECOUNTER-001")
    assert result.checks["counterexamples_present"] is False
    assert result.checks["primary_scenario_present"] is True
    assert result.scenarios == {"primary": 1, "counterexample": 1, "total": 2}


def test_placeholder_text_does_not_satisfy_a_section(fixture_config):
    result = evaluate(fixture_config, "PLACEHOLDER-001")
    assert result.checks["intent_defined"] is False
    assert any("scaffolding text" in f.message for f in result.failures)


def test_a_scenario_with_no_assertion_withholds_readiness(fixture_config):
    result = evaluate(fixture_config, "NOTHEN-001")
    assert result.checks["assertions_are_determinable"] is False
    assert any(f.rule == "missing-then" for f in result.failures)


def test_amigos_running_withholds_readiness_from_a_complete_contract(fixture_config):
    result = evaluate(fixture_config, "RUNNING-001")
    assert all(result.checks.values()), "the contract itself is complete"
    assert result.ready is False
    assert result.state == "amigos_running"
    assert result.exit_code == dor.EXIT_NOT_READY


def test_contract_change_also_withholds_readiness(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    path = cfg.story_dir("READY-001") / "state.json"
    data = json.loads(path.read_text())
    data["declared_state"] = "contract_change"
    path.write_text(json.dumps(data))
    result = dor.evaluate(cfg, "READY-001")
    assert all(result.checks.values())
    assert result.ready is False
    assert result.state == "contract_change"


@pytest.mark.parametrize("story_id,fragment", [
    ("MISSING-001", "missing contract file"),
    ("SELFPROMO-001", "not declarable"),
    ("UNTAGGED-001", "roles cannot be counted"),
    ("BADGHERKIN-001", "outside the supported Gherkin subset"),
    ("NO-SUCH-STORY", "story not found"),
])
def test_structural_defects_raise_instead_of_producing_a_verdict(
    fixture_config, story_id, fragment
):
    with pytest.raises(dor.StructuralError) as excinfo:
        evaluate(fixture_config, story_id)
    assert fragment in str(excinfo.value)


def test_no_dor_is_written_for_a_structural_defect(scratch_repo):
    from amigos.cli import main
    code = main(["check", "--root", str(scratch_repo), "SELFPROMO-001"])
    assert code == dor.EXIT_STRUCTURAL
    assert not (scratch_repo / ".amigos" / "stories" / "SELFPROMO-001" / "dor.json").exists()


def test_generated_dor_satisfies_its_schema(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    schema = jsonschema.load_schema("dor.schema.json")
    for story_id in ("READY-001", "BLOCKED-001", "VAGUE-001", "RUNNING-001"):
        payload = dor.evaluate(cfg, story_id).as_dict()
        assert jsonschema.validate(payload, schema) == [], story_id


def test_dor_records_a_hash_of_every_contract_input(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    payload = dor.evaluate(cfg, "READY-001").as_dict()
    assert set(payload["contract_hash"]) == set(story.HASHED_FILES)


def test_evaluation_is_deterministic_across_runs(fixture_config):
    first = evaluate(fixture_config, "VAGUE-001")
    second = evaluate(fixture_config, "VAGUE-001")
    assert first.checks == second.checks
    assert [f.as_dict() for f in first.failures] == [f.as_dict() for f in second.failures]
    assert first.exit_code == second.exit_code


def test_write_produces_the_only_dor_file(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    result = dor.evaluate(cfg, "READY-001")
    path = dor.write(result)
    assert path.name == "dor.json"
    assert json.loads(path.read_text())["ready"] is True


def test_thresholds_are_configurable(scratch_repo):
    config_path = scratch_repo / ".amigos" / "config.json"
    data = json.loads(config_path.read_text())
    data["dor"]["min_counterexamples"] = 1
    config_path.write_text(json.dumps(data))
    cfg = config_module.load(root=scratch_repo)
    assert dor.evaluate(cfg, "ONECOUNTER-001").checks["counterexamples_present"] is True


def test_missing_constraints_sections_withhold_readiness(scratch_repo):
    cfg = config_module.load(root=scratch_repo)
    path = cfg.story_dir("READY-001") / "constraints.md"
    path.write_text("# Constraints\n\n## Technical Constraints\n\n## Dependencies\n")
    result = dor.evaluate(cfg, "READY-001")
    assert result.checks["constraints_defined"] is False
