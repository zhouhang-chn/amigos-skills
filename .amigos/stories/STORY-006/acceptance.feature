Feature: Implementation from a ready contract

  @primary
  Scenario: A ready contract reaches verified implementation
    Given a story whose contract satisfies every Definition of Ready check
    When the implement skill runs to completion
    Then the run names, for every scenario in acceptance.feature, the test or judgement method that decides it
    And the repository test suite passes
    And the sha256 of each of the four contract input files equals the hash recorded in dor.json before the run

  @primary
  Scenario: A test for absent behaviour fails before the source changes
    Given a ready contract whose primary scenario describes behaviour this repository does not yet have
    When the run writes that scenario's test and executes it against the unchanged source
    Then that test fails
    And the run records the failing result before any governed file is modified
    And the same test passes once the behaviour is implemented

  @primary
  Scenario: A verification command decides whether the requirement was redefined
    Given a story whose dor.json recorded a hash for each contract input file
    When the verification command is run for that story
    Then it re-evaluates readiness from the contract files rather than reading the recorded verdict
    And it names every contract input file whose sha256 differs from the recorded hash
    And it exits non-zero when at least one file differs

  @counterexample
  Scenario: A story that is not ready gets no implementation
    Given a story whose contract carries an unresolved blocking question
    When the implement skill is invoked for that story
    Then no governed file is modified
    And the run names the story and the check that failed
    And no test file is added for that story

  @counterexample
  Scenario: A readiness verdict recorded in the story is not trusted on its own
    Given dor.json in the story directory records ready true
    And acceptance.feature has since lost a counterexample
    When the implement skill is invoked for that story
    Then no governed file is modified
    And the run reports the verdict it reached by re-evaluating the contract files, not the verdict dor.json recorded

  @counterexample
  Scenario: A contract conflict stops the run instead of editing the contract
    Given a Then clause that contradicts a constraint in the same contract
    When the run reaches that scenario
    Then acceptance.feature is byte-identical to the file whose hash dor.json recorded
    And the run names the scenario and the clause it conflicts with
    And state.json declares contract_change
    And the run stops without invoking the amigos skill

  @counterexample
  Scenario: An unsatisfied scenario is reported rather than made green
    Given a test derived from a Then clause that the implementation does not satisfy
    When the run finishes
    Then that test is present in the suite, unskipped, and reported as failing
    And the run lists that scenario as unsatisfied
    And the run does not report the story as implemented

  @counterexample
  Scenario: A change no scenario requires is reported as scope expansion
    Given a ready contract whose scenarios and constraints do not mention an adjacent behaviour
    When the run reports the files it changed
    Then every changed governed file is listed with the scenario or constraint it serves
    And a changed file that serves neither is listed under scope expansion
    And the run continues to completion rather than stopping at that file

  @counterexample
  Scenario: A Then no test can observe is named rather than dropped
    Given a scenario whose Then describes behaviour no test in this repository can observe
    When the run reports coverage
    Then that scenario is listed with the judgement method used in place of a test
    And it is excluded from the count of scenarios decided by tests

  @counterexample
  Scenario: The run takes no privileged path around the gate
    Given the gate refuses an edit because no active story resolves
    When the run responds to the refusal
    Then the settings file holding the gate hook is byte-for-byte unchanged
    And the pre-commit hook is byte-for-byte unchanged
    And no commit is created with the pre-commit hook skipped
    And the run reports the gate's message and the story id it could not resolve
