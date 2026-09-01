export const attestationFailureScenarios = [
  {
    code: 'DATA_REQUIREMENT_NOT_MET',
    stage: 'Evaluation',
    reason: 'The payload is missing the required subjectId field.',
    evidence: 'payload.subjectId is required by the contract schema.',
    action: 'Add subjectId to the payload and submit the attestation again.',
    retryable: false
  },
  {
    code: 'DATA_REQUIREMENT_NOT_MET',
    stage: 'Evaluation',
    reason: 'The observation is older than the contract freshness limit.',
    evidence: 'Observed age: 19 minutes. Contract limit: 10 minutes.',
    action: 'Send a current observation or review the freshness limit.',
    retryable: false
  },
  {
    code: 'DATA_REQUIREMENT_NOT_MET',
    stage: 'Evaluation',
    reason: 'A measured value is outside the configured range.',
    evidence: 'temperature was 11.8. Allowed range: 2 to 8.',
    action: 'Correct the measurement or review the configured range.',
    retryable: false
  },
  {
    code: 'DATA_REQUIREMENT_NOT_MET',
    stage: 'Evaluation',
    reason: 'The JQ quality expression returned success false.',
    evidence: 'The expression found an empty dataProvider value.',
    action: 'Provide a dataProvider value that satisfies the expression.',
    retryable: false
  },
  {
    code: 'DATA_REQUIREMENT_NOT_MET',
    stage: 'Evaluation',
    reason: 'The tabular expectation did not pass.',
    evidence: '2 of 14 rows contained an invalid riskScore value.',
    action: 'Correct the invalid rows and submit the data again.',
    retryable: false
  },
  {
    code: 'EVALUATION_OPERATIONAL_FAULT',
    stage: 'Processing',
    reason: 'The processing service could not run the evaluation.',
    evidence: 'No evaluation result was produced for the request.',
    action: 'Check the processing service and retry.',
    retryable: true
  }
]

export const verificationFailureScenarios = [
  {
    code: 'AOV_SIGNATURE_INVALID',
    reason: 'The attestation signature could not be accepted.',
    evidence: 'The requested contract_id attribute was not accepted by the verifier.',
    action: 'Confirm the issuer key and request a valid attestation.',
    retryable: false
  },
  {
    code: 'DATA_COMMITMENT_MISMATCH',
    reason: 'The attestation was created for different data.',
    evidence: 'The attested data hash does not match the received payload hash.',
    action: 'Request an attestation created for the received data.',
    retryable: false
  },
  {
    code: 'VLA_COMMITMENT_MISMATCH',
    reason: 'The claims do not match the referenced VLA version.',
    evidence: 'The verified claims use a different VLA commitment.',
    action: 'Request an attestation for the committed VLA version.',
    retryable: false
  },
  {
    code: 'SIGNATURE_VERIFICATION_FAILED',
    reason: 'Signature verification did not return a valid result.',
    evidence: 'The request is waiting for a peer response.',
    action: 'Inspect the verification evidence before retrying.',
    retryable: true
  }
]
