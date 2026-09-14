Feature: A contract state change leaves evidence, and a blocked story permits no work

  @primary
  Scenario: A declared state the history does not record is refused
    Given a ready story whose state.json history records only draft
    And a state.json whose declared_state has been set to contract_change by hand
    When a change to that story's acceptance.feature is put to the gate
    Then the exit code is 1
    And the refusal names that story id
    And the refusal names state.json
    And the refusal names contract_change as a declaration the history does not record
    And the refusal does not tell the caller to make the story ready

  @primary
  Scenario: A history entry removed after it was committed is refused
    Given a story whose committed state.json records three history entries
    And a working tree state.json holding only the first and the second
    And a declared_state matching the second entry
    When a change to a governed source file is put to the gate for that story
    Then the exit code is 1
    And the refusal names state.json
    And the refusal names the state of the removed entry

  @primary
  Scenario: A governed change under a blocked story is refused with the route out
    Given a story that fails at least one Definition of Ready check
    And that the gate resolves that story as the active story
    When a change to a governed source file is put to the gate as an uncommitted edit
    And the same change is put to the gate as a staged set
    Then both exit codes are 1
    And both refusals report that story's derived state as blocked
    And both refusals name a failed Definition of Ready check by its check name
    And both refusals name the amigos skill as the route out

  @counterexample
  Scenario: A reopening recorded through the state command is permitted
    Given a ready story reopened by running the state command with contract_change
    When a change to that story's acceptance.feature is put to the gate
    Then the exit code is 0
    And running the state command for that story with no transition exits 0
    And that story's state.json is byte-identical to what the state command wrote

  @counterexample
  Scenario: Declaring contract_change still reopens a frozen contract
    Given a ready story whose acceptance.feature the gate has refused to change
    When contract_change is declared for that story through the state command
    And the same change to that story's acceptance.feature is put to the gate
    Then the write that declared contract_change is permitted
    And the exit code for the change to acceptance.feature is 0

  @counterexample
  Scenario: The commit that would launder a rewritten history is refused
    Given a story whose committed state.json records three history entries
    And a staged state.json holding only the first and the second
    When the staged set is put to the gate
    Then the exit code is 1
    And the refusal names state.json

  @counterexample
  Scenario: A write to the story's own state.json is permitted while the record is inconsistent
    Given a story whose declared_state disagrees with its last history entry
    When a change to that story's state.json is put to the gate
    Then the exit code is 0
    And a change to that story's acceptance.feature put to the gate exits 1

  @counterexample
  Scenario: A state.json that cannot be parsed is refused rather than permitted
    Given a ready story whose state.json is not valid JSON
    When a change to that story's acceptance.feature is put to the gate
    Then the exit code is 1
    And the refusal names state.json

  @counterexample
  Scenario: A state.json that was never committed is not reported as inconsistent
    Given a story scaffolded from the templates and left uncommitted
    When a change to a governed source file is put to the gate for that story
    Then no refusal names state.json
    And running the state command for that story with no transition exits 2

  @counterexample
  Scenario: No declarable state makes a blocked story permit a governed change
    Given a story that fails at least one Definition of Ready check
    When draft, amigos_running and contract_change are each declared for it in turn
    And a change to a governed source file is put to the gate after each
    Then all three exit codes are 1
    And no run reports that story as ready

  @counterexample
  Scenario: Every story in this repository passes the consistency rule
    Given this repository's own stories directory
    When the state command runs with no transition for each story it holds
    Then every exit code is 0
    And no output names a declaration the history does not record

  @counterexample
  Scenario: The report writes nothing
    Given a story whose declared_state disagrees with its last history entry
    When the state command runs for that story with no transition
    Then the exit code is 1
    And every file in that story's directory is byte-identical to before the run
