Feature: Student grades cover enough unique students
  As a data consumer
  I want a VLA requiring grade data to cover at least 25 unique students
  So that I only accept grade data that is complete enough to be representative

  # The check counts distinct student IDs, not rows: a student with several
  # grades is counted once.  Uses the "Minimum unique values" template; the
  # template and the VLAs are created once and shared by every scenario.
  #
  # Two VLAs, because the edge node demo attests two data sets: the anonymized xAPI
  # statements (the student is actor.account.name) and the aggregated rows, one per
  # student (the student is name).  Neither VLA checks the other's data.

  Background:
    * def provider = 'http://dva-api-provider:9090'
    * def uuid = function() { return java.util.UUID.randomUUID() + '' }
    # `rows` xAPI statements spread over `students` distinct students (rows >= students); the
    # student is identified by actor.account.name
    * def grades = function(students, rows) { var r = []; for (var i = 0; i < rows; i++) { r.push({ id: java.util.UUID.randomUUID() + '', actor: { objectType: 'Agent', account: { homePage: 'https://neptun.example.edu', name: 's' + (i % students) } }, verb: { id: 'http://adlnet.gov/expapi/verbs/passed' }, result: { score: { raw: 3 + (i % 3) } } }) } return r }

    # `students` aggregated rows, as the aggregation service makes them: one per student
    * def aggregated = function(students) { var r = []; for (var i = 0; i < students; i++) { r.push({ name: 's' + i, events: 1 + (i % 5), result: (i % 2 == 0 ? 'passed' : 'failed'), grade: 1 + (i % 4) }) } return r }

    # The template and the VLAs are created once for all scenarios below
    * def template = read('../test-data/vla-template/min-unique-values.json')
    * def setup = callonce read('helpers/grades-vla.feature') { template: '#(template)' }
    * def templateID = setup.templateID
    * def vlaID = setup.vlaID
    * def aggregatedVlaID = setup.aggregatedVlaID
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

  Scenario Outline: aggregated data, <case>
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(aggregatedVlaID)', data: '#(aggregated(<students>))' }
    When method post
    Then status 200
    And match response.evaluationPassing == <passes>
    And match response.evaluationResults == '#[1]'
    And match response.evaluationResults[0] contains { engine: 'JQ', success: <passes> }
    And match response.evaluationResults[0].details contains 'found <students> distinct name values, need at least 25'
    And match response.jws == (<passes> ? '#string' : '#notpresent')

    Examples:
      | case                                       | students | passes |
      | exactly 25 students                        | 25       | true   |
      | more than 25 students                      | 30       | true   |
      | one student short of the minimum           | 24       | false  |
      | no data at all                             | 0        | false  |

  Scenario: aggregated rows are not checked by the VLA for anonymized statements
    # The rows have no actor.account.name, so they count as a single (missing) student
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(vlaID)', data: '#(aggregated(30))' }
    When method post
    Then status 200
    And match response.evaluationPassing == false
    And match response.evaluationResults[0].details contains 'found 1 distinct actor.account.name values, need at least 25'
    And match response.jws == '#notpresent'

  Scenario: anonymized statements are not checked by the VLA for aggregated data
    # The statements have no name, so they count as a single (missing) student
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(aggregatedVlaID)', data: '#(grades(30, 30))' }
    When method post
    Then status 200
    And match response.evaluationPassing == false
    And match response.evaluationResults[0].details contains 'found 1 distinct name values, need at least 25'
    And match response.jws == '#notpresent'
