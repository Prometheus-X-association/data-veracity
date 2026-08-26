const DEFINITIONS = {
  EVALUATION_PENDING: { status: 'pending', title: 'Evaluation is still processing', summary: 'The request was accepted, but no completed evaluation is available yet.', nextAction: 'Wait for processing to finish, then refresh the record.', retryable: true },
  SCHEMA_VALIDATION_FAILED: { status: 'failed', title: 'Data does not match the required schema', summary: 'One or more required fields or value types do not match the contract.', nextAction: 'Compare the data with the schema, correct the payload, and submit it again.', retryable: false },
  JQ_CHECK_FAILED: { status: 'failed', title: 'JQ quality check failed', summary: 'The JQ expression returned a failed result for this data.', nextAction: 'Review the expression and the referenced values before sending the data again.', retryable: false },
  GREAT_EXPECTATIONS_FAILED: { status: 'failed', title: 'Great Expectations check failed', summary: 'The tabular quality expectation did not pass for the supplied data.', nextAction: 'Review the expectation details and the JSON to table mapping, then correct the data.', retryable: false },
  TEMPLATE_RENDER_FAILED: { status: 'failed', title: 'Requirement could not be rendered', summary: 'The template could not be turned into a complete quality requirement.', nextAction: 'Check the template variables and try rendering it again.', retryable: false },
  INVALID_TEMPLATE_INPUT: { status: 'invalid', title: 'Template input is invalid', summary: 'A template variable is missing or has the wrong value type.', nextAction: 'Fill in the highlighted fields with values that match the template definition.', retryable: false },
  UNKNOWN_TEMPLATE: { status: 'unavailable', title: 'Template was not found', summary: 'The selected template is not available in the current gateway.', nextAction: 'Refresh the template list or choose another template.', retryable: true },
  MISSING_REQUIRED_DATA: { status: 'invalid', title: 'Required data is missing', summary: 'The request does not contain all information required by the contract.', nextAction: 'Add the missing field or select a contract that matches this data.', retryable: false },
  FRESHNESS_FAILED: { status: 'failed', title: 'Data is outside the freshness limit', summary: 'The timestamp is older or newer than the contract allows.', nextAction: 'Send a current observation or review the freshness limit in the contract.', retryable: false },
  RANGE_FAILED: { status: 'failed', title: 'Value is outside the allowed range', summary: 'A measured value is below the minimum or above the maximum in the contract.', nextAction: 'Correct the value or review the configured range.', retryable: false },
  VERIFICATION_REJECTED: { status: 'failed', title: 'Presentation was rejected', summary: 'The verifier received a presentation but could not accept its claims.', nextAction: 'Review the requested attributes and ask the holder for a current credential.', retryable: false },
  VERIFICATION_PENDING: { status: 'pending', title: 'Verification is still pending', summary: 'The presentation exchange has started but no final result is available.', nextAction: 'Wait for the exchange to finish and refresh the verification.', retryable: true },
  CREDENTIAL_REVOKED: { status: 'failed', title: 'Credential is revoked', summary: 'The credential was found, but its issuer no longer considers it valid.', nextAction: 'Request a replacement credential before retrying the verification.', retryable: false },
  GATEWAY_UNAVAILABLE: { status: 'unavailable', title: 'Gateway is unavailable', summary: 'The dashboard could not reach the DVA gateway.', nextAction: 'Check the gateway status and try again when the service is available.', retryable: true },
  PROCESSING_TIMEOUT: { status: 'error', title: 'Processing timed out', summary: 'The evaluation did not return within the expected time.', nextAction: 'Retry once the processing service is healthy. Keep the request ID for support.', retryable: true },
  QUEUE_FAILURE: { status: 'error', title: 'Request could not enter the processing queue', summary: 'The gateway accepted the request but could not hand it to the processing service.', nextAction: 'Retry when the gateway and message transport are healthy.', retryable: true },
  PERSISTENCE_FAILURE: { status: 'error', title: 'Result could not be saved', summary: 'The evaluation completed, but the result could not be written to storage.', nextAction: 'Do not assume the result is recorded. Retry and keep the request ID.', retryable: true },
  UNKNOWN_FAILURE: { status: 'error', title: 'The operation failed', summary: 'The service returned an error without a more specific failure reason.', nextAction: 'Review the evidence, check the gateway status, and retry if the data is valid.', retryable: true }
}

function asText (value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  try { return JSON.stringify(value) } catch { return String(value) }
}

function evidenceFrom (value, fallback) {
  const text = asText(value) || asText(fallback)
  return text || 'No additional evidence was returned.'
}

export function failureFromCode (code = 'UNKNOWN_FAILURE', context = {}) {
  const definition = DEFINITIONS[code] || DEFINITIONS.UNKNOWN_FAILURE
  return { code: DEFINITIONS[code] ? code : 'UNKNOWN_FAILURE', status: context.status || definition.status, title: context.title || definition.title, summary: context.summary || definition.summary, evidence: evidenceFrom(context.evidence, context.error || context.details), nextAction: context.nextAction || definition.nextAction, retryable: context.retryable ?? definition.retryable, source: context.source || 'gateway' }
}

export function normalizeEvaluationResult (result = {}, context = {}) {
  if (context.pending || result.pending) return failureFromCode('EVALUATION_PENDING', context)
  if (result.success === true) return { code: null, status: 'passed', title: 'Evaluation passed', summary: 'All checks in this evaluation passed.', evidence: evidenceFrom(result.details, 'The quality engine returned success.'), nextAction: 'No action is required.', retryable: false, source: context.source || 'gateway' }
  const engine = String(result.engine || '').toUpperCase()
  const text = `${asText(result.error)} ${asText(result.details)}`.toLowerCase()
  let code = context.code
  if (!code && (text.includes('fresh') || text.includes('age') || text.includes('timestamp'))) code = 'FRESHNESS_FAILED'
  if (!code && (text.includes('range') || text.includes('minimum') || text.includes('maximum') || text.includes('between'))) code = 'RANGE_FAILED'
  if (!code && (text.includes('required') || text.includes('schema') || engine === 'SCHEMA')) code = 'SCHEMA_VALIDATION_FAILED'
  if (!code && engine === 'JQ') code = 'JQ_CHECK_FAILED'
  if (!code && (engine === 'GREAT_EXPECTATIONS' || engine === 'GREATEXPECTATIONS')) code = 'GREAT_EXPECTATIONS_FAILED'
  if (!code && (text.includes('timeout') || text.includes('timed out'))) code = 'PROCESSING_TIMEOUT'
  if (!code) code = 'UNKNOWN_FAILURE'
  return failureFromCode(code, { ...context, evidence: [result.error, result.details].filter(Boolean).map(asText).join(' | ') })
}

export { DEFINITIONS as failureDefinitions }
