import test from 'node:test'
import assert from 'node:assert/strict'
import { normalizeAttestationRecord } from '../src/failures/failureModel.js'
import { fromRequestLog, fromRequestLogs } from '../src/requestLog.js'

// Entries shaped like `GET /info/requests` of the synchronous DVA API.
const base = {
  type: 'ATTESTATION_REQUEST',
  exchangeID: 'a8f1c7a0-0000-4000-8000-000000000001',
  contractID: 'a8f1c7a0-0000-4000-8000-000000000002',
  vlaID: 'a8f1c7a0-0000-4000-8000-000000000003',
  receivedDate: '2026-11-09T15:40:04.478758Z'
}
const passing = {
  ...base,
  id: 'log-pass',
  evaluationPassing: true,
  vcID: 'vc-1',
  evaluationResults: [{ engine: 'JQ', success: true, details: 'ok' }]
}
const failingData = {
  ...base,
  id: 'log-bad',
  evaluationPassing: false,
  evaluationResults: [{ engine: 'SCHEMA', success: false, details: "'actor' is a required property" }]
}
const unknownVla = {
  ...base,
  id: 'log-missing',
  evaluationPassing: false,
  evaluationResults: [],
  error: { title: 'Resource Not Found', detail: 'VLA ee39d793-b3b0-4fdb-8789-b4009325dce6 not found' }
}

test('maps the API log fields to the dashboard record shape', () => {
  const record = fromRequestLog(passing)
  assert.equal(record.requestID, 'log-pass')
  assert.equal(record.evaluationDate, passing.receivedDate)
  assert.deepEqual(fromRequestLogs(null), [])
})

test('a logged passing request is passed, not pending', () => {
  const record = normalizeAttestationRecord(fromRequestLog(passing))
  assert.equal(record.status, 'passed')
})

test('a logged request with failed checks is failed with the check evidence, not pending', () => {
  const record = normalizeAttestationRecord(fromRequestLog(failingData))
  assert.equal(record.status, 'failed')
  assert.equal(record.failure.code, 'SCHEMA_VALIDATION_FAILED')
  assert.match(record.failure.evidence, /actor/)
})

test('a logged request for an unknown VLA is reported as such, not pending', () => {
  const mapped = fromRequestLog(unknownVla)
  assert.equal(mapped.evaluationDate, null)
  const record = normalizeAttestationRecord(mapped)
  assert.equal(record.status, 'unavailable')
  assert.equal(record.failure.code, 'VLA_NOT_FOUND')
  assert.match(record.failure.evidence, /ee39d793/)
})

test('any other logged error is an unknown failure with its detail as evidence', () => {
  const record = normalizeAttestationRecord(fromRequestLog({
    ...unknownVla,
    error: { title: 'Upstream service error', detail: 'VC_MANAGER returned 400 Bad Request' }
  }))
  assert.equal(record.failure.code, 'UNKNOWN_FAILURE')
  assert.match(record.failure.evidence, /VC_MANAGER/)
})
