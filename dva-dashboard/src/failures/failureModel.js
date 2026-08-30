const DEFINITIONS = {
  DATA_REQUIREMENT_NOT_MET: ['failed', 'Data does not fulfil the VLA', 'Review the failed checks, correct the data, and submit it again.', false, 'evaluation'],
  EVALUATION_OPERATIONAL_FAULT: ['error', 'Evaluation could not run', 'Check the processing service and its dependencies before retrying.', true, 'evaluation'],
  EVALUATION_TRANSIENT_FAULT: ['error', 'Evaluation may be inconsistent', 'Retry the evaluation and compare the results. Escalate repeated differences.', true, 'evaluation'],
  EVALUATION_LOGIC_SYNTAX_INVALID: ['invalid', 'Evaluation logic is invalid', 'Correct and validate the requirement implementation before using the VLA.', false, 'requirement'],
  EVALUATION_LOGIC_INCORRECT: ['error', 'Evaluation logic checks the wrong condition', 'Stop using this VLA version and review the implementation against the requirement.', false, 'requirement'],
  REQUIREMENT_MISUNDERSTOOD: ['error', 'The VLA does not express the intended requirement', 'Confirm the intended rule with its author and publish a corrected VLA version.', false, 'requirement'],
  AOV_ISSUANCE_OPERATIONAL_FAULT: ['error', 'The attestation could not be issued', 'Check signing configuration and the VC Manager, then retry issuance.', true, 'issuance'],
  AOV_MALFORMED: ['invalid', 'The attestation is malformed', 'Reject it and ask the issuer for a correctly formed attestation.', false, 'attestation'],
  AOV_SIGNATURE_INVALID: ['failed', 'The attestation signature is invalid', 'Do not trust the attestation. Confirm the issuer key and request a replacement.', false, 'attestation'],
  SIGNATURE_VERIFICATION_FAILED: ['failed', 'Signature verification failed', 'Do not use the attestation. Inspect the verification evidence and issuer key.', false, 'verification'],
  DATA_COMMITMENT_MISMATCH: ['failed', 'The attestation refers to different data', 'Reject it and request an attestation created for the received data.', false, 'verification'],
  VLA_COMMITMENT_MISMATCH: ['failed', 'Claims do not match the referenced VLA version', 'Reject it and verify the claims against the committed VLA version.', false, 'verification'],
  AOV_CLAIMS_FORGED: ['warning', 'Attestation claims may be false', 'Treat this as a trust incident. Re-evaluate the data independently if necessary.', false, 'trust'],
  UNKNOWN_FAILURE: ['error', 'The operation failed', 'Review the returned evidence and service logs before deciding whether to retry.', false, 'unknown']
}

export const failureHierarchy = Object.freeze({
  requirement: ['EVALUATION_LOGIC_SYNTAX_INVALID', 'EVALUATION_LOGIC_INCORRECT', 'REQUIREMENT_MISUNDERSTOOD'],
  evaluation: ['DATA_REQUIREMENT_NOT_MET', 'EVALUATION_OPERATIONAL_FAULT', 'EVALUATION_TRANSIENT_FAULT'],
  issuance: ['AOV_ISSUANCE_OPERATIONAL_FAULT'],
  attestation: ['AOV_MALFORMED', 'AOV_SIGNATURE_INVALID'],
  verification: ['SIGNATURE_VERIFICATION_FAILED', 'DATA_COMMITMENT_MISMATCH', 'VLA_COMMITMENT_MISMATCH'],
  trust: ['AOV_CLAIMS_FORGED']
})

function evidenceFrom (...values) {
  const value = values.find(item => item !== undefined && item !== null && item !== '')
  if (value === undefined) return 'No additional evidence was returned.'
  if (typeof value === 'string') return value
  try { return JSON.stringify(value) } catch { return String(value) }
}

export function failureFromCode (code, context = {}) {
  const resolvedCode = Object.hasOwn(DEFINITIONS, code) ? code : 'UNKNOWN_FAILURE'
  const [status, title, nextAction, retryable, category] = DEFINITIONS[resolvedCode]
  return { code: resolvedCode, category, status: context.status || status, title: context.title || title, summary: context.summary || title, evidence: evidenceFrom(context.evidence, context.details, context.error), nextAction: context.nextAction || nextAction, retryable: context.retryable ?? retryable, source: context.source || category }
}

function successfulResult (source, evidence) {
  return { code: null, category: source, status: 'passed', title: 'Check passed', summary: 'The check completed successfully.', evidence: evidenceFrom(evidence), nextAction: 'No action is required.', retryable: false, source }
}

export function normalizeAttestationRecord (record = {}) {
  const code = record.failureCode || record.failure_code || record.error?.code
  const passed = record.evaluationPassing === true || record.status === 'passed' || record.success === true
  const failure = passed ? successfulResult('evaluation', record.evaluationResults || record.result) : failureFromCode(code, record)
  return { ...record, status: failure.status, failure }
}

export function normalizeVerificationRecord (record = {}) {
  const response = record.response || {}
  const code = record.failureCode || record.failure_code || response.failure_code || response.error?.code
  const verified = record.verified === true || response.verified === true || response.success === true
  const failure = verified ? successfulResult('verification', response) : failureFromCode(code, { ...record, evidence: response })
  return { ...record, status: failure.status, failure }
}

export const failureDefinitions = Object.freeze(DEFINITIONS)
