Feature: TODO name the behaviour under contract

  # Every scenario must carry exactly one of @primary or @counterexample.
  # A ready story needs at least 1 @primary and at least 2 @counterexample scenarios.
  # Then clauses must be independently judgeable: state the observable outcome,
  # not that it was "handled correctly".

  @primary
  Scenario: TODO the main path
    Given TODO a relevant starting state
    When TODO the action or event
    Then TODO an externally judgeable outcome

  @counterexample
  Scenario: TODO a plausible nearby failure
    Given TODO a relevant starting state
    When TODO the action that should not succeed
    Then TODO the observable rejection
    And TODO what must remain unchanged

  @counterexample
  Scenario: TODO a second, distinct failure class
    Given TODO a relevant starting state
    When TODO the action that should not succeed
    Then TODO the observable rejection
