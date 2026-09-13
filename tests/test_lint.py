import pytest

from amigos import config as config_module
from amigos.gherkin import parse
from amigos.lint import failures, lint_feature

GOOD = """Feature: Access control

  @primary
  Scenario: Authorised caller
    Given an authenticated user
    When the user reads their own record
    Then the API returns HTTP 200

  @counterexample
  Scenario: Foreign record
    Given an authenticated user
    When the user reads another user's record
    Then the API returns HTTP 403
    And no account data is modified
"""


def lint(text, cfg):
    return lint_feature(parse(text, "acceptance.feature"), cfg)


def rules(findings):
    return [f.rule for f in findings]


def test_judgeable_contract_produces_no_findings(fixture_config):
    assert lint(GOOD, fixture_config) == []


def test_vague_assertion_is_reported_with_line_and_word(fixture_config):
    text = GOOD.replace("    Then the API returns HTTP 200",
                        "    Then the request is handled correctly")
    findings = lint(text, fixture_config)
    assert rules(findings) == ["vague-assertion"]
    assert findings[0].line == 7
    assert findings[0].word == "correctly"
    assert findings[0].severity == "failure"


def test_vague_word_in_a_setup_step_does_not_fire(fixture_config):
    text = GOOD.replace("    Given an authenticated user\n    When the user reads their own",
                        "    Given a request that was handled well\n    When the user reads their own")
    assert lint(text, fixture_config) == []


def test_vague_word_in_an_and_continuing_a_then_does_fire(fixture_config):
    text = GOOD.replace("    And no account data is modified",
                        "    And the audit trail is proper")
    findings = lint(text, fixture_config)
    assert rules(findings) == ["vague-assertion"]
    assert findings[0].word == "proper"


def test_matching_is_bounded_to_whole_words(fixture_config):
    text = GOOD.replace("    Then the API returns HTTP 200",
                        "    Then the incorrectness counter increments")
    assert lint(text, fixture_config) == []


def test_multi_word_vocabulary_matches_across_whitespace(fixture_config):
    text = GOOD.replace("    Then the API returns HTTP 200",
                        "    Then the retry is handled    well")
    assert [f.word for f in lint(text, fixture_config)] == ["handled well"]


def test_scenario_without_a_then_is_reported(fixture_config):
    text = GOOD.replace("    Then the API returns HTTP 403\n", "")
    text = text.replace("    And no account data is modified\n", "")
    findings = lint(text, fixture_config)
    assert "missing-then" in rules(findings)
    assert findings[0].line == 10


def test_untagged_scenario_is_reported_at_the_scenario_line(fixture_config):
    text = GOOD.replace("  @counterexample\n  Scenario: Foreign record", "  Scenario: Foreign record")
    findings = lint(text, fixture_config)
    assert rules(findings) == ["untagged-scenario"]
    assert findings[0].line == 9


def test_a_scenario_carrying_both_roles_is_reported(fixture_config):
    text = GOOD.replace("  @counterexample\n", "  @primary @counterexample\n")
    assert rules(lint(text, fixture_config)) == ["ambiguous-tag"]


def test_empty_step_is_reported(fixture_config):
    text = GOOD.replace("    Then the API returns HTTP 200", "    Then")
    findings = lint(text, fixture_config)
    # One defect, one finding: an empty Then is still a Then, so missing-then
    # stays quiet and empty-step carries the report.
    assert rules(findings) == ["empty-step"]
    assert findings[0].line == 7


def test_then_before_when_is_only_a_warning(fixture_config):
    text = """Feature: F

  @primary
  Scenario: Out of order
    Given a state
    Then the record exists
    When the job runs
"""
    findings = lint(text, fixture_config)
    assert rules(findings) == ["then-before-when"]
    assert failures(findings) == []


def test_findings_are_ordered_by_line(fixture_config):
    text = GOOD.replace("    Then the API returns HTTP 200", "    Then it works")
    text = text.replace("    And no account data is modified", "    And it is good")
    lines = [f.line for f in lint(text, fixture_config)]
    assert lines == sorted(lines)


def test_repository_can_extend_the_vocabulary(repo_root, tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text(
        '{"lint": {"vague_words_extra": ["as designed"]}}', encoding="utf-8")
    cfg = config_module.load(root=tmp_path)
    text = GOOD.replace("    Then the API returns HTTP 200", "    Then the job finishes as designed")
    assert [f.word for f in lint(text, cfg)] == ["as designed"]


def test_repository_can_shorten_the_vocabulary(tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text(
        '{"lint": {"vague_words_remove": ["works"]}}', encoding="utf-8")
    cfg = config_module.load(root=tmp_path)
    assert "works" not in cfg.vague_words
    text = GOOD.replace("    Then the API returns HTTP 200", "    Then the pipeline works")
    assert lint(text, cfg) == []


def test_background_steps_are_linted_for_vocabulary(fixture_config):
    text = """Feature: F

  Background:
    Given a tenant
    Then setup completed properly

  @primary
  Scenario: S
    When it runs
    Then the row exists
"""
    findings = lint(text, fixture_config)
    assert rules(findings) == ["vague-assertion"]


def test_background_is_not_required_to_carry_a_role_tag(fixture_config):
    text = """Feature: F

  Background:
    Given a tenant

  @primary
  Scenario: S
    When it runs
    Then the row exists

  @counterexample
  Scenario: T
    When it fails
    Then the row is absent
"""
    assert lint(text, fixture_config) == []
