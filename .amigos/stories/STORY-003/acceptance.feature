Feature: Acceptance criteria linting

  @primary
  Scenario: A judgeable assertion passes the lint
    Given a tagged scenario whose assertion states that the API returns HTTP 403
    When lint_acceptance checks the file
    Then the command exits with code 0
    And no findings are reported

  @counterexample
  Scenario: A vague assertion fails the lint
    Given a tagged scenario asserting that the result is handled correctly
    When lint_acceptance checks the file
    Then the command exits with code 1
    And a vague-assertion finding is reported
    And the finding carries the line number of the offending step
    And the finding names the offending word

  @counterexample
  Scenario: A scenario with no assertion fails the lint
    Given a tagged scenario containing a Given step and a When step and no Then step
    When lint_acceptance checks the file
    Then the command exits with code 1
    And a missing-then finding names the scenario and its line number

  @counterexample
  Scenario: Vague vocabulary in a setup step does not fire the rule
    Given a tagged scenario whose Given step describes a request that was handled well
    And that scenario asserts that the response body is empty
    When lint_acceptance checks the file
    Then the command exits with code 0
    And the vague-assertion rule reports nothing

  @counterexample
  Scenario: A scenario declaring no role fails the lint
    Given a scenario tagged neither @primary nor @counterexample
    When lint_acceptance checks the file
    Then the command exits with code 1
    And an untagged-scenario finding carries the line number of the scenario
