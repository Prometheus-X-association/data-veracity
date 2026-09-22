Feature: Health endpoints
  Every DVA service answers /livez and /readyz with {status, output};
  see docs/health-checks.md.

  Scenario Outline: <base> is alive and ready
    Given url '<base>'
    And path 'livez'
    When method get
    Then status 200
    And match header Content-Type contains 'application/health+json'
    And match response == { status: 'pass' }

    Given url '<base>'
    And path 'readyz'
    When method get
    Then status 200
    And match response == { status: 'pass' }

    Examples:
      | base                                |
      | http://dva-api-provider:9090        |
      | http://dva-api-consumer:9090        |
      | http://dva-processing-provider:5000 |
      | http://dva-vc-manager:8000          |
      | http://vla-manager-api:8000         |
      | http://dva-dashboard-provider       |
      | http://vla-manager                  |
