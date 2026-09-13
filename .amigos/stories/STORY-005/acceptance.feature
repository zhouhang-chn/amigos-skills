Feature: Independent Three Amigos subagents

  @primary
  Scenario: The three roles draft without seeing each other
    Given a story id and a description
    When the drafting phase runs
    Then the Product, Development and QA agents each receive the ticket and repository access
    And no agent's prompt contains another agent's output

  @primary
  Scenario: A run records each role's findings separately
    Given a completed drafting phase
    When the reconciliation pass runs
    Then the run holds one findings record per role
    And each finding names its role, target file, target section and risk dimension

  @counterexample
  Scenario: Two roles naming the same thing count as one finding
    Given two roles that name the same target section and the same risk dimension
    When the overlap is counted
    Then that finding is counted as shared
    And it is absent from the count of findings named by exactly one role

  @counterexample
  Scenario: A run in which the split adds nothing says so
    Given a run in which every finding is named by more than one role
    When the run reports its findings summary
    Then the count of findings named by exactly one role is 0
    And the summary states that no role contributed a finding the others missed

  @counterexample
  Scenario: A drafting agent that returns nothing stops the run
    Given one of the three agents returns no findings record
    When the reconciliation pass is reached
    Then the run stops before writing any contract file
    And state.json holds the declaration it carried before the drafting phase

  @counterexample
  Scenario: Reconciliation cannot grant readiness
    Given a reconciled contract that fails a Definition of Ready check
    When the skill finishes
    Then dor.json records ready false
    And dor.json was written by the validator rather than by any agent

  @counterexample
  Scenario: A conflict between roles reaches the contract
    Given Product places a behaviour in scope
    And Development reports that behaviour as not buildable as described
    When the reconciliation pass resolves the conflict
    Then the contract records a narrowed scope or a blocking question
    And no commentary file is written into the story directory
