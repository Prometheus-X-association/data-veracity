export const attestationFailureScenarios = [
  {
    code: 'SCHEMA_VALIDATION_FAILED',
    stage: 'Evaluation',
    reason: 'The payload is missing the required subjectId field.',
    evidence: 'payload.subjectId is required by the contract schema.',
    action: 'Add subjectId to the payload and submit the attestation again.',
    retryable: false
  },
  {
    code: 'FRESHNESS_FAILED',
    stage: 'Evaluation',
    reason: 'The observation is older than the contract freshness limit.',
    evidence: 'Observed age: 19 minutes. Contract limit: 10 minutes.',
    action: 'Send a current observation or review the freshness limit.',
    retryable: false
  },
  {
    code: 'RANGE_FAILED',
    stage: 'Evaluation',
    reason: 'A measured value is outside the configured range.',
    evidence: 'temperature was 11.8. Allowed range: 2 to 8.',
    action: 'Correct the measurement or review the configured range.',
    retryable: false
  },
  {
    code: 'JQ_CHECK_FAILED',
    stage: 'Evaluation',
    reason: 'The JQ quality expression returned success false.',
    evidence: 'The expression found an empty dataProvider value.',
    action: 'Provide a dataProvider value that satisfies the expression.',
    retryable: false
  },
  {
    code: 'GREAT_EXPECTATIONS_FAILED',
    stage: 'Evaluation',
    reason: 'The tabular expectation did not pass.',
    evidence: '2 of 14 rows contained an invalid riskScore value.',
    action: 'Correct the invalid rows and submit the data again.',
    retryable: false
  },
  {
    code: 'QUEUE_FAILURE',
    stage: 'Processing',
    reason: 'The gateway could not place the request on the processing queue.',
    evidence: 'The request was accepted but no processing receipt was created.',
    action: 'Check gateway and message transport health, then retry.',
    retryable: true
  }
]

export const verificationFailureScenarios = [
  {
    code: 'VERIFICATION_REJECTED',
    reason: 'The presentation did not satisfy the requested attributes.',
    evidence: 'The requested contract_id attribute was not accepted by the verifier.',
    action: 'Ask the holder for a presentation that includes the current contract.',
    retryable: false
  },
  {
    code: 'CREDENTIAL_REVOKED',
    reason: 'The presented credential was revoked by its issuer.',
    evidence: 'Credential status returned by the issuer: revoked.',
    action: 'Request a replacement credential before retrying.',
    retryable: false
  },
  {
    code: 'MISSING_REQUIRED_DATA',
    reason: 'The presentation did not include all requested attributes.',
    evidence: 'attr_data_exchange_id was not revealed in the presentation.',
    action: 'Request a complete presentation from the holder.',
    retryable: false
  },
  {
    code: 'VERIFICATION_PENDING',
    reason: 'The presentation exchange has not returned a final result.',
    evidence: 'The request is waiting for a peer response.',
    action: 'Wait for the exchange to finish and refresh the verification.',
    retryable: true
  }
]
