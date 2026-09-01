import test from 'node:test'
import assert from 'node:assert/strict'

import { failureFromCode, failureHierarchy, normalizeAttestationRecord, normalizeVerificationRecord } from '../dva-dashboard/src/failures/failureModel.js'
import { verificationFailureScenarios } from '../dva-dashboard/src/failures/demoFailures.js'

test('groups failures by the stage where feedback belongs', () => {
  assert.ok(failureHierarchy.requirement.includes('EVALUATION_LOGIC_SYNTAX_INVALID'))
  assert.ok(failureHierarchy.evaluation.includes('EVALUATION_TRANSIENT_FAULT'))
  assert.ok(failureHierarchy.verification.includes('DATA_COMMITMENT_MISMATCH'))
})

test('uses explicit codes without inferring a cause from prose', () => {
  assert.equal(failureFromCode(undefined, { error: 'signature mismatch' }).code, 'UNKNOWN_FAILURE')
  assert.equal(failureFromCode('AOV_SIGNATURE_INVALID').category, 'attestation')
})

test('reads structured VC Manager verification results', () => {
  const record = normalizeVerificationRecord({ response: { verified: false, failure_code: 'VLA_COMMITMENT_MISMATCH' } })
  assert.equal(record.failure.code, 'VLA_COMMITMENT_MISMATCH')
  assert.equal(record.failure.retryable, false)
})

test('preserves failure details returned with an evaluation request', () => {
  const record = normalizeAttestationRecord({
    evaluationPassing: false,
    failureCode: 'DATA_REQUIREMENT_NOT_MET',
    failureReason: 'The observation is too old.',
    failureEvidence: 'Observed age: 19 minutes. Contract limit: 10 minutes.',
    recommendedAction: 'Send a current observation.',
    failureRetryable: false
  })

  assert.equal(record.failure.summary, 'The observation is too old.')
  assert.equal(record.failure.evidence, 'Observed age: 19 minutes. Contract limit: 10 minutes.')
  assert.equal(record.failure.nextAction, 'Send a current observation.')
  assert.equal(record.failure.retryable, false)
})

test('represents an unfinished evaluation as pending', () => {
  const record = normalizeAttestationRecord({
    status: 'pending',
    failureCode: 'EVALUATION_PENDING',
    failureReason: 'The request is waiting for the evaluation processor.',
    failureEvidence: 'No evaluation result has been written yet.',
    recommendedAction: 'Refresh after processing completes.',
    failureRetryable: true
  })

  assert.equal(record.failure.code, 'EVALUATION_PENDING')
  assert.equal(record.failure.status, 'pending')
  assert.equal(record.failure.evidence, 'No evaluation result has been written yet.')
})

test('preserves verification evidence when the response is empty', () => {
  const record = normalizeVerificationRecord({
    verified: false,
    response: {},
    failureCode: 'DATA_COMMITMENT_MISMATCH',
    failureReason: 'The data hash does not match.',
    failureEvidence: 'Expected sha256:abc, received sha256:def.',
    recommendedAction: 'Request an attestation for the received data.'
  })

  assert.equal(record.failure.summary, 'The data hash does not match.')
  assert.equal(record.failure.evidence, 'Expected sha256:abc, received sha256:def.')
  assert.equal(record.failure.nextAction, 'Request an attestation for the received data.')
})

test('uses data commitment evidence for the data commitment demo', () => {
  const scenario = verificationFailureScenarios.find(item => item.code === 'DATA_COMMITMENT_MISMATCH')

  assert.match(scenario.evidence, /hash/i)
  assert.doesNotMatch(scenario.evidence, /revoked/i)
})
