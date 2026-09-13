Feature: Definition of Ready validation

  @primary
  Scenario: Ready story passes validation
    Given a story contains all required contract files
    And all required checks pass
    And no blocking questions remain
    When check_dor validates the story
    Then the command exits with code 0
    And dor.json ready is true
    And dor.json state is "ready"

  @counterexample
  Scenario: Blocking question prevents readiness
    Given a story whose open-questions.md lists an item under Blocking
    When check_dor validates the story
    Then the command exits with code 1
    And dor.json ready is false
    And dor.json blocking_questions contains that item

  @counterexample
  Scenario: A single counterexample is not enough
    Given acceptance.feature contains one @primary scenario and one @counterexample scenario
    When check_dor validates the story
    Then the command exits with code 1
    And dor.json checks.counterexamples_present is false

  @counterexample
  Scenario: A story failing the acceptance lint is not ready
    Given acceptance.feature contains a scenario the linter rejects
    When check_dor validates the story
    Then the command exits with code 1
    And dor.json checks.assertions_are_determinable is false
    And dor.json failures cites acceptance.feature with a line number

  @counterexample
  Scenario: A declared state of amigos_running withholds readiness
    Given a story whose contract files satisfy every check
    And state.json declares the state amigos_running
    When check_dor validates the story
    Then the command exits with code 1
    And dor.json state is "amigos_running"
    And dor.json ready is false

  @counterexample
  Scenario: A missing contract file is reported as a structural defect
    Given a story directory without constraints.md
    When check_dor validates the story
    Then the command exits with code 2
    And dor.json is not written
    And the message names the missing file
