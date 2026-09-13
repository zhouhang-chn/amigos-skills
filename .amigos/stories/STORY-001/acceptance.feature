Feature: Story contract workspace and schema

  @primary
  Scenario: Scaffolding a story produces the full contract input set
    Given a repository containing .amigos/config.json
    And no story directory named STORY-999
    When create_story scaffolds STORY-999
    Then .amigos/stories/STORY-999 contains intent.md, constraints.md, acceptance.feature, open-questions.md and state.json
    And state.json declared_state is "draft"
    And dor.json is absent

  @counterexample
  Scenario: An unedited scaffold does not satisfy the Definition of Ready
    Given a story scaffolded from the templates with no edits
    When the validator evaluates the story
    Then the exit code is 1
    And dor.json ready is false

  @counterexample
  Scenario: Scaffolding refuses to overwrite an existing story
    Given a story directory named STORY-999 already exists
    When create_story is asked to scaffold STORY-999
    Then the exit code is 2
    And every file already in .amigos/stories/STORY-999 is byte-for-byte unchanged

  @counterexample
  Scenario: An agent cannot declare readiness in state.json
    Given state.json in a story declares the state ready
    When the validator evaluates the story
    Then the exit code is 2
    And dor.json is not written
    And the message names state.json as the rejected file
