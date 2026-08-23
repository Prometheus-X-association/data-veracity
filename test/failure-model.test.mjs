import test from 'node:test'
import assert from 'node:assert/strict'
import {
  normalizeAttestationRecord,
  normalizeEvaluationResult,
  normalizeVerificationRecord
} from '../dva-dashboard/src/failures/failureModel.js'

test('explains a schema evaluation failure with evidence and recovery guidance', () => {
  const failure = normalizeEvaluationResult({
    engine: 'SCHEMA',
    success: false,
    error: 'required property is missing',
    details: 'payload.userId is required'
  }, { requestId: 'req-1' })

  assert.equal(failure.status, 'failed')
  assert.equal(failure.code, 'SCHEMA_VALIDATION_FAILED')
  assert.match(failure.evidence, /userId/i)
  assert.match(failure.nextAction, /payload|schema/i)
  assert.equal(failure.retryable, false)
})

test('keeps an unevaluated attestation pending instead of calling it failed', () => {
  const record = normalizeAttestationRecord({
    requestID: 'req-2',
    evaluationDate: null,
    evaluationPassing: null
  })

  assert.equal(record.status, 'pending')
  assert.equal(record.failure.code, 'EVALUATION_PENDING')
  assert.equal(record.failure.retryable, true)
})

test('explains a rejected verification separately from a missing presentation', () => {
  const rejected = normalizeVerificationRecord({
    thread_id: 'thread-1',
    verified: false
  })
  const pending = normalizeVerificationRecord({
    thread_id: 'thread-2',
    verified: null,
    status: 'pending'
  })

  assert.equal(rejected.failure.code, 'VERIFICATION_REJECTED')
  assert.equal(rejected.status, 'failed')
  assert.equal(pending.failure.code, 'VERIFICATION_PENDING')
  assert.equal(pending.status, 'pending')
})
