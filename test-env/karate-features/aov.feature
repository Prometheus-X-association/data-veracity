Feature: Attestation of Veracity (AoV) generation


Background:
  * url 'http://dva-api:9090'
  * def exampleRequestGood = read('../test-data/aov/timestamp_in_range/request-good.json')
  * def exampleRequestBad = read('../test-data/aov/timestamp_in_range/request-bad.json')


Scenario: create an AoV request with data passing requirements

  Given path 'attestation'
  And request exampleRequestGood
  When method post
  Then status 200
  And match response == { id: '#uuid' }

  * def id = response.id

  * configure retry = { count: 5, interval: 1000 }
  Given url 'http://callback-dummy'
  And path 'get/last'
  And retry until responseStatus == 200
  When method get


Scenario: create an AoV request with data failing requirements

  Given path 'attestation'
  And request exampleRequestBad
  When method post
  Then status 200
  And match response == { id: '#uuid' }

  * def id = response.id

  * configure retry = { count: 5, interval: 1000 }
  Given url 'http://callback-dummy'
  And path 'get/last'
  And retry until responseStatus == 200
  When method get
