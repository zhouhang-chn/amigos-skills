Feature: A story is judged against the contract in git history

  @primary
  Scenario: An unchanged contract verifies against its committed baseline
    Given a story whose four contract files are committed and match the working tree
    When the verification command runs for that story
    Then the exit code is 0
    And the output reports verified true
    And the output names the git revision the four files were compared against
    And no file inside the story directory is written

  @primary
  Scenario: The baseline is the parent of the first governed change
    Given a story whose contract was committed before any governed file changed
    And a later commit that changes a governed path for that story
    When the verification command resolves the baseline revision
    Then the resolved revision is the parent of that later commit

  @counterexample
  Scenario: Re-running the readiness check does not launder a contract edit
    Given a story whose contract is committed and whose implementation has begun
    And acceptance.feature differs from its committed content
    When the readiness check runs and then the verification command runs
    Then the exit code is 1
    And the output names acceptance.feature as differing from the baseline

  @counterexample
  Scenario: A contract edit committed during implementation does not become the baseline
    Given a story whose implementation has begun in an earlier commit
    And a commit after it that changes acceptance.feature
    When the verification command runs for that story
    Then the exit code is 1
    And the output names acceptance.feature as differing from the baseline

  @counterexample
  Scenario: A contract that was never committed is unanswerable
    Given a story whose four contract files appear in no commit
    When the verification command runs for that story
    Then the exit code is 2
    And the output states that no committed contract was found for that story

  @counterexample
  Scenario: A readiness verdict written by hand produces no pass
    Given a story whose committed acceptance.feature has lost a counterexample in the working tree
    And dor.json in that story directory records ready true
    When the verification command runs for that story
    Then the exit code is 1
    And the output reports ready false

  @counterexample
  Scenario: A change outside the story directory is not a contract change
    Given a story whose four contract files match their committed content
    And uncommitted changes to source files and test files elsewhere in the repository
    When the verification command runs for that story
    Then the exit code is 0
    And every path named as compared is inside that story's directory

  @counterexample
  Scenario: A contract rewritten through contract_change stays verifiable
    Given a story that was reopened by declaring contract_change and rewritten
    And the rewritten contract is committed before any further governed change
    When the verification command runs for that story
    Then the exit code is 0
    And restoring the superseded contract text in the working tree raises the exit code to 1

  @counterexample
  Scenario: A configured content filter does not produce a difference
    Given a repository configured to normalise line endings on checkout
    And a story whose committed contract matches the working tree under that filter
    When the verification command runs for that story
    Then the exit code is 0
