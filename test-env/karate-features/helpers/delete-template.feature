@ignore
Feature: Delete a template
  # Called with { templateID }; not a test itself.

  Scenario: delete the template
    Given url 'http://vlamanager-backend:8000'
    And path 'template', templateID
    When method delete
    Then status 204
