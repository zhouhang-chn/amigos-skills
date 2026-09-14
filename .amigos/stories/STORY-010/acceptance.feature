Feature: The gate refuses a contract edit while a story is ready

  @primary
  Scenario: An edit to a ready story's acceptance criteria is refused
    Given a story whose Definition of Ready passes every check
    When a change to that story's acceptance.feature is put to the gate
    Then the exit code is 1
    And the refusal names acceptance.feature
    And the refusal names that story id
    And the refusal names the declaration that reopens the contract
    And the refusal does not tell the caller to make the story ready

  @primary
  Scenario: Declaring a withholding state reopens the contract
    Given a ready story whose acceptance.feature the gate has refused to change
    When contract_change is declared for that story through the state command
    And the same change to that story's acceptance.feature is put to the gate
    Then the write that declared contract_change was permitted
    And the exit code for the second change is 0

  @counterexample
  Scenario: An edit that would leave the story unready is refused all the same
    Given a ready story whose contract is committed
    And a working tree in which acceptance.feature has lost one counterexample
    When the staged change to that file is put to the gate
    Then the exit code is 1
    And the refusal names acceptance.feature
    And the refusal names no failed Definition of Ready check

  @counterexample
  Scenario: The commit that first records a ready contract is permitted
    Given a story whose contract has just been written and passes every check
    And no commit reachable from HEAD holds that story's acceptance.feature
    When a staged set holding that story's four contract files is put to the gate
    Then the exit code is 0

  @counterexample
  Scenario: A story that is not ready keeps an editable contract
    Given a story whose Definition of Ready fails at least one check
    When a change to each of its four contract files is put to the gate in turn
    Then every exit code is 0

  @counterexample
  Scenario: Only the contract inputs are frozen, not the records beside them
    Given a story that is ready
    When the gate is asked about a rewritten dor.json for that story
    And the gate is asked about a rewritten state.json for that story
    And the gate is asked about a new file under that story's run directory
    Then every one of those three exit codes is 0
    And a change to that story's acceptance.feature exits 1

  @counterexample
  Scenario: The refusal follows the story the path names, not the active one
    Given a ready story that the gate resolves as the active story
    And a second ready story that the gate does not resolve as active
    When a change to the second story's acceptance.feature is put to the gate
    Then the exit code is 1
    And the refusal names the second story id

  @counterexample
  Scenario: A story whose contract cannot be evaluated stays editable
    Given a story whose acceptance.feature no longer parses as Gherkin
    And a path under the stories directory naming a story id that has no directory
    When a change to each of those two paths is put to the gate
    Then every exit code is 0

  @counterexample
  Scenario: A staged deletion of a ready story's contract file is refused
    Given a ready story whose four contract files are committed
    And a staged deletion of that story's acceptance.feature
    When the staged set is put to the gate
    Then the exit code is 1
    And the refusal names acceptance.feature

  @counterexample
  Scenario: Scaffolding a new story is permitted while another story is ready
    Given a repository in which every existing story is ready
    When a new story directory and its five scaffolded files are put to the gate
    Then the exit code is 0
