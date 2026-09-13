Feature: A fixture contract

  @primary
  Scenario: The main path
    Given an authenticated user
    When the user submits a valid request
    Then the response status is 200

  @counterexample
  Scenario: An invalid request
    Given an authenticated user
    When the user submits an invalid request
    Then the response status is 400
    And no record is written

  Scenario: An unauthenticated request
    Given an anonymous caller
    When the caller submits a request
    Then the response status is 401
