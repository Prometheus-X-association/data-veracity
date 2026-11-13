Feature: Attestation of Veracity (AoV) issuance and verification
  As a data provider in a given data exchange
  I want to attest that the data I send satisfies the VLA of the exchange
  So that the consumer can verify the resulting Attestation of Veracity (AoV)

  # Replaces the former aov_gen / aov_present features, which targeted the
  # asynchronous, ACA-Py based API.  The current API is synchronous:
  #   POST /attestation        -> { jws?, evaluationPassing, evaluationResults }
  #   POST /attestation/verify -> { verified, reason? }
  # Verification only succeeds when the consumer's VC Manager trusts the
  # provider's did:key; the Background sets that up once, together with the
  # VLA shared by every scenario (helpers/attestation-setup.feature).

  Background:
    * def provider = 'http://dva-api-provider:9090'
    * def consumer = 'http://dva-api-consumer:9090'
    * def uuid = function() { return java.util.UUID.randomUUID() + '' }

    # The provider's key is whitelisted on the consumer and the VLA is created
    # once, for all scenarios below
    * def setup = callonce read('helpers/attestation-setup.feature')
    * def vlaID = setup.vlaID

    * def goodData = { timestamp: '20250301T0000Z', result: 3 }
    * def badData = { timestamp: '20240101T0000Z', result: 9 }

  Scenario: data satisfying the VLA is attested and the AoV verifies
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(vlaID)', data: '#(goodData)' }
    When method post
    Then status 200
    And match response.evaluationPassing == true
    And match response.jws == '#string'
    And match response.evaluationResults == '#[2]'
    And match each response.evaluationResults contains { engine: 'JQ', success: true }
    * def jws = response.jws

    Given url consumer
    And path 'attestation', 'verify'
    And request { jws: '#(jws)' }
    When method post
    Then status 200
    And match response == { verified: true }

  Scenario: data violating the VLA yields no AoV
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(vlaID)', data: '#(badData)' }
    When method post
    Then status 200
    And match response.evaluationPassing == false
    And match response.jws == '#notpresent'
    And match response.evaluationResults contains { engine: 'JQ', success: false, timestamp: '#string', details: '#string' }

  Scenario: an attestation request is logged by the provider
    * def exchangeID = uuid()
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(exchangeID)', contractID: '#(uuid())', vlaID: '#(vlaID)', data: '#(goodData)' }
    When method post
    Then status 200

    Given url provider
    And path 'info', 'requests'
    When method get
    Then status 200
    * def matching = karate.filter(response, function(log) { return log.exchangeID == exchangeID })
    And match matching == '#[1]'
    And match matching[0] contains { type: 'ATTESTATION_REQUEST', vlaID: '#(vlaID)', evaluationPassing: true, vcID: '#string' }

  Scenario: an AoV whose signature was altered does not verify
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(vlaID)', data: '#(goodData)' }
    When method post
    Then status 200
    * def jws = response.jws
    # Replace the first character of the signature (third JWS segment)
    * def i = jws.lastIndexOf('.') + 1
    * def tampered = jws.substring(0, i) + (jws.charAt(i) == 'A' ? 'B' : 'A') + jws.substring(i + 1)

    Given url consumer
    And path 'attestation', 'verify'
    And request { jws: '#(tampered)' }
    When method post
    Then status 200
    And match response.verified == false
    And match response.reason == '#string'

  Scenario: an attestation request for an unknown VLA is rejected
    Given url provider
    And path 'attestation'
    And request { exchangeID: '#(uuid())', contractID: '#(uuid())', vlaID: '#(uuid())', data: '#(goodData)' }
    When method post
    Then status 404
