Feature: Amigos contract orchestration

  @primary
  Scenario: A described story becomes a ready contract
    Given a story id and a description with no unresolved ambiguity
    When the amigos skill runs to completion
    Then the story directory holds intent.md, constraints.md, acceptance.feature and open-questions.md
    And the validator exits with code 0
    And state.json declares draft

  @primary
  Scenario: A lifecycle transition is recorded
    Given a story whose state.json declares draft
    When the state command sets the declared state to amigos_running
    Then state.json declares amigos_running
    And the previous entry remains in the history

  @counterexample
  Scenario: An unanswerable question blocks the story
    Given a description whose authorisation behaviour is unspecified
    And the interview does not resolve it
    When the amigos skill runs to completion
    Then open-questions.md lists that question under Blocking
    And the validator exits with code 1
    And intent.md states no assumption about authorisation

  @counterexample
  Scenario: The skill cannot grant its own readiness
    Given a story whose contract fails a Definition of Ready check
    When the amigos skill finishes
    Then dor.json records ready false
    And dor.json was written by the validator rather than the skill

  @counterexample
  Scenario: The state command refuses a state it does not own
    Given a story whose state.json declares draft
    When the state command is asked to set the declared state to ready
    Then the exit code is 2
    And state.json still declares draft

  @counterexample
  Scenario: Reopening a story keeps what came before
    Given a story that has already been through the skill once
    When the skill reopens it for revision
    Then state.json declares contract_change
    And the earlier history entries are still present

  @counterexample
  Scenario: A repair loop that cannot converge stops
    Given a contract the validator rejects on every attempt
    When the skill exhausts its repair attempts
    Then the skill reports the remaining findings
    And the story is left with state.json declaring draft
