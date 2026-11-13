@ignore
Feature: Set up attestation tests
  # Called once by attestation.feature (callonce); not a test itself.
  # Returns { providerDidKey, vlaID }.

  Scenario: trust the provider's key on the consumer and create the VLA
    # The consumer's VC Manager has to trust the provider's signing key
    Given url 'http://dva-vc-manager-provider:8000'
    And path 'admin', 'keys'
    When method get
    Then status 200
    * def providerDidKey = response.issuer_did_key

    Given url 'http://dva-vc-manager-consumer:8000'
    And path 'admin', 'whitelist'
    And request { did_key: '#(providerDidKey)', label: 'provider' }
    When method post
    Then status 201

    # A VLA with two JQ checks: recent timestamp, and result in [1, 5].
    # Defined here rather than read from test-data/vla-request/request.json,
    # whose JQ is not evaluable (single-quoted string, no `details`).
    * def recentCheck = { type: 'custom', engine: 'JQ', implementation: '{ success: (.timestamp >= \"20250101T0000Z\"), details: \"timestamp must not be before 2025-01-01\" }' }
    * def rangeCheck = { type: 'custom', engine: 'JQ', implementation: '{ success: (.result >= 1 and .result <= 5), details: \"result must be between 1 and 5\" }' }
    * def vla = { name: 'Recent and valid data', description: { purpose: 'Attestation test' }, schema: [{ name: 'data', logicalType: 'object', properties: [{ name: 'timestamp', logicalType: 'string' }, { name: 'result', logicalType: 'integer' }], quality: ['#(recentCheck)', '#(rangeCheck)'] }] }
    Given url 'http://vlamanager-backend:8000'
    And path 'vla'
    And request vla
    When method post
    Then status 201
    * def vlaID = response.id
