import pytest

from amigos.gherkin import ParseError, parse

BASE = """Feature: Billing

  @primary
  Scenario: Happy path
    Given an account
    When the email changes
    Then the email is stored
    And the account id is unchanged
"""


def test_records_feature_and_scenario_lines():
    feature = parse(BASE, "f.feature")
    assert feature.name == "Billing"
    assert feature.line == 1
    assert [s.line for s in feature.scenarios] == [4]
    assert feature.scenarios[0].tags == ("@primary",)


def test_step_lines_are_one_based_and_exact():
    steps = parse(BASE, "f.feature").scenarios[0].steps
    assert [(s.keyword, s.line) for s in steps] == [
        ("Given", 5), ("When", 6), ("Then", 7), ("And", 8),
    ]


def test_and_inherits_the_keyword_it_continues():
    steps = parse(BASE, "f.feature").scenarios[0].steps
    assert steps[3].effective_keyword == "Then"
    assert steps[3].is_assertion
    assert not steps[0].is_assertion


def test_and_after_given_is_not_an_assertion():
    text = BASE.replace("    When the email changes\n",
                        "    And a billing address\n    When the email changes\n")
    steps = parse(text, "f.feature").scenarios[0].steps
    assert steps[1].keyword == "And"
    assert steps[1].effective_keyword == "Given"
    assert not steps[1].is_assertion


def test_roles_expose_only_contract_tags():
    text = BASE.replace("  @primary", "  @primary @slow")
    scenario = parse(text, "f.feature").scenarios[0]
    assert scenario.tags == ("@primary", "@slow")
    assert scenario.roles == ("@primary",)


def test_background_is_separate_from_scenarios():
    text = """Feature: B

  Background:
    Given a tenant

  @primary
  Scenario: S
    When it happens
    Then it is recorded
"""
    feature = parse(text, "f.feature")
    assert feature.background is not None
    assert feature.background.steps[0].text == "a tenant"
    assert len(feature.scenarios) == 1


def test_doc_string_content_is_not_read_as_gherkin():
    text = BASE + '''
  @counterexample
  Scenario: With a payload
    Given a request
      """
      Feature: this is data, not gherkin
      Then this must not become a step
      """
    When it is sent
    Then the status is 400
'''
    feature = parse(text, "f.feature")
    assert len(feature.scenarios) == 2
    assert [s.keyword for s in feature.scenarios[1].steps] == ["Given", "When", "Then"]


def test_data_table_rows_attach_without_becoming_steps():
    text = BASE + """
  @counterexample
  Scenario: Tabular
    Given these accounts
      | id | plan |
      | 1  | free |
    When billing runs
    Then no invoice is created
"""
    scenario = parse(text, "f.feature").scenarios[1]
    assert [s.keyword for s in scenario.steps] == ["Given", "When", "Then"]


def test_scenario_outline_requires_examples():
    text = """Feature: F

  @primary
  Scenario Outline: Parametrised
    Given <account>
    Then it is stored
"""
    with pytest.raises(ParseError) as excinfo:
        parse(text, "f.feature")
    assert "no Examples block" in str(excinfo.value)


def test_scenario_outline_with_examples_parses():
    text = """Feature: F

  @primary
  Scenario Outline: Parametrised
    Given <account>
    Then it is stored

    Examples:
      | account |
      | a       |
"""
    feature = parse(text, "f.feature")
    assert feature.scenarios[0].keyword == "Scenario Outline"
    assert feature.scenarios[0].examples_line == 8


@pytest.mark.parametrize("text,fragment", [
    ("Scenario: orphan\n    Given a thing\n", "before the Feature"),
    ("Feature: F\n\n  Rule: grouping\n", "outside the supported Gherkin subset"),
    ("Feature: F\n\n  Given a step\n", "outside a Scenario"),
    ("Feature: F\n\n  @primary\n  Scenario: S\n    And it continues nothing\n",
     "no preceding Given, When or Then"),
    ("Feature: F\n\n  @primary\n  Scenario: S\n    Given a\n    Then b\n  Examples:\n",
     "without a preceding Scenario Outline"),
    ("Feature: F\n\n  @primary\n  Scenario: S\n    Given a\n      \"\"\"\n      unterminated\n",
     "never closed"),
    ("Feature: F\n\n  @primary\n", "not followed by a Scenario"),
    ("# only a comment\n", "no Feature found"),
    ("Feature: F\n\n  @primary\n  Scenario: S\n    Given a\n    Then b\n  nonsense line\n",
     "unrecognised line"),
    ("Feature: A\n\nFeature: B\n", "exactly one Feature"),
])
def test_unsupported_constructs_raise_rather_than_being_skipped(text, fragment):
    with pytest.raises(ParseError) as excinfo:
        parse(text, "f.feature")
    assert fragment in str(excinfo.value)


def test_parse_error_carries_the_line_number():
    with pytest.raises(ParseError) as excinfo:
        parse("Feature: F\n\n  @primary\n  Scenario: S\n    Given a\n  Rule: x\n", "f.feature")
    assert excinfo.value.line == 6
    assert "f.feature:6" in str(excinfo.value)
