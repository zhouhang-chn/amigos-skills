Feature: Repository gate on source changes

  @primary
  Scenario: A governed change under a ready story is permitted
    Given the active story resolves to a story whose contract satisfies every check
    When the gate evaluates a change to a governed file
    Then the exit code is 0

  @primary
  Scenario: The environment overrides the branch name
    Given AMIGOS_STORY names a ready story
    And the branch name contains a different story id
    When the gate resolves the active story
    Then the resolved story is the one AMIGOS_STORY names

  @counterexample
  Scenario: A governed change under a story that is not ready is refused
    Given the active story resolves to a story with an unresolved blocking question
    When the gate evaluates a change to a governed file
    Then the exit code is 1
    And the message names the story and the check that failed

  @counterexample
  Scenario: A governed change with no resolvable story is refused
    Given no story id is set in the environment or the pointer file
    And the branch name contains no story id
    When the gate evaluates a change to a governed file
    Then the exit code is 1
    And the message lists the three places a story id is read from

  @counterexample
  Scenario: A change touching only exempt paths needs no story
    Given no story id can be resolved
    When the gate evaluates a change to a file under docs
    Then the exit code is 0

  @counterexample
  Scenario: A path in no configured directory is governed anyway
    Given a changed file in a directory named in no configuration
    And the active story has an unresolved blocking question
    When the gate evaluates the change
    Then the exit code is 1

  @counterexample
  Scenario: A branch naming two stories is refused
    Given the branch name contains two story ids
    When the gate resolves the active story
    Then the exit code is 1
    And the message names both candidates

  @counterexample
  Scenario: A stale committed verdict does not permit a change
    Given a story directory whose dor.json records ready true
    And acceptance.feature has since lost its counterexamples
    When the gate evaluates a change to a governed file
    Then the exit code is 1

  @counterexample
  Scenario: Installing the git hook preserves an existing one
    Given .git/hooks/pre-commit exists and was not written by amigos
    When the hook installation runs without a forcing flag
    Then the exit code is 2
    And the existing hook file is byte-for-byte unchanged
