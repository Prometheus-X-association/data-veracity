Feature: Student grades cover enough unique students
  As a data consumer
  I want a VLA requiring grade data to cover at least 25 unique students
  So that I only accept grade data that is complete enough to be representative

  # The check counts distinct student IDs, not rows: a student with several
  # grades is counted once.  Uses the "Minimum unique values" template; the
  # template and the VLA are created once and shared by every scenario.

  Background:
    * def provider = 'http://dva-api-provider:9090'
    * def uuid = function() { return java.util.UUID.randomUUID() + '' }
    # `rows` xAPI statements spread over `students` distinct students (rows >= students); the
    # student is identified by actor.account.name
    * def grades = function(students, rows) { var r = []; for (var i = 0; i < rows; i++) { r.push({ id: java.util.UUID.randomUUID() + '', actor: { objectType: 'Agent', account: { homePage: 'https://neptun.example.edu', name: 's' + (i % students) } }, verb: { id: 'http://adlnet.gov/expapi/verbs/passed' }, result: { score: { raw: 3 + (i % 3) } } }) } return r }

    # The template and the VLA are created once for all scenarios below
    * def template = read('../test-data/vla-template/min-unique-values.json')
    * def setup = callonce read('helpers/grades-vla.feature') { template: '#(template)' }
    * def templateID = setup.templateID
    * def vlaID = setup.vlaID
    * configure afterFeature = function() { karate.call('helpers/delete-template.feature', { templateID: templateID }) }

  Scenario Outline: <case>
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(vlaID)', data: '#(grades(<students>, <rows>))' }
    When method post
    Then status 200
    And match response.evaluationPassing == <passes>
    And match response.evaluationResults == '#[1]'
    And match response.evaluationResults[0] contains { engine: 'JQ', success: <passes> }
    And match response.evaluationResults[0].details contains 'found <students> distinct actor.account.name values, need at least 25'
    # An AoV is issued only when the requirement is satisfied
    And match response.jws == (<passes> ? '#string' : '#notpresent')

    Examples:
      | case                                       | students | rows | passes |
      | exactly 25 unique students                 | 25       | 25   | true   |
      | more than 25, several grades per student   | 30       | 90   | true   |
      | one student short of the minimum           | 24       | 24   | false  |
      | many rows but only 24 unique students      | 24       | 100  | false  |
      | a single student                           | 1        | 50   | false  |
      | no data at all                             | 0        | 0    | false  |
