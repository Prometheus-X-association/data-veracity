@ignore
Feature: Set up the "25 unique students" VLAs
  # Called once by grades_unique_students.feature (callonce); not a test itself.
  # Called with { template }, the template definition; returns { templateID, vlaID, aggregatedVlaID }:
  # the VLA for the anonymized statements (the student is actor.account.name) and the one for
  # the aggregated data (the student is name).  One VLA cannot check both: the paths differ.

  Scenario: create the template and the VLAs built from it
    Given url 'http://vlamanager-backend:8000'
    And path 'template'
    And request __arg.template
    When method post
    Then status 201
    * def templateID = response.id

    Given url 'http://vlamanager-backend:8000'
    And path 'vla', 'from-templates'
    And request { name: 'Rulebook L3 edge:gate-min-cohort', description: { purpose: 'The number of contributors in a cohort is at least 25' }, qualityTemplates: [{ id: '#(templateID)', model: { field: 'actor.account.name', minimum: 25 } }] }
    When method post
    Then status 201
    * def vlaID = response.id

    Given url 'http://vlamanager-backend:8000'
    And path 'vla', 'from-templates'
    And request { name: 'Rulebook L3 edge:gate-min-cohort (aggregated)', description: { purpose: 'The number of students in the aggregated data is at least 25' }, qualityTemplates: [{ id: '#(templateID)', model: { field: 'name', minimum: 25 } }] }
    When method post
    Then status 201
    * def aggregatedVlaID = response.id
