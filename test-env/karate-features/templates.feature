Feature: Veracity Level Agreement (VLA) template management


Background:
  * url 'http://dva-api:9090'
  * def exampleTemplate = read('../test-data/vla-template/template.json')


Scenario: get all VLA templates

  Given path 'template'
  When method get
  Then status 200


Scenario: create, get, then delete VLA template

  Given path 'template'
  And request exampleTemplate
  When method post
  Then status 201
  And match response == { id: '#string' }

  * def id = response.id

  Given path 'template', id
  When method get
  Then status 200
  And match response == exampleTemplate
  
  Given path 'template'
  When method get
  Then status 200
  And match response contains exampleTemplate
