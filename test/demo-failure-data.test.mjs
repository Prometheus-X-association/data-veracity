import test from 'node:test'
import assert from 'node:assert/strict'
import { demoCredentials, demoPresentations, demoRequests } from '../dva-dashboard/src/demoData.js'

test('demo attestations include passed, pending, and explained failure records', () => {
  const states = new Set(demoRequests.map(record => record.status))
  const codes = new Set(demoRequests.map(record => record.failureCode).filter(Boolean))

  assert.deepEqual([...states].sort(), ['failed', 'passed', 'pending'])
  assert.ok(codes.has('SCHEMA_VALIDATION_FAILED'))
  assert.ok(codes.has('FRESHNESS_FAILED'))
  assert.ok(codes.has('QUEUE_FAILURE'))
  assert.ok(demoRequests.every(record => record.status === 'passed' || record.failureReason))
})

test('demo verifications and credentials expose pending and revoked states', () => {
  assert.ok(demoPresentations.some(record => record.status === 'pending'))
  assert.ok(demoPresentations.some(record => record.status === 'failed' && record.failureCode === 'VERIFICATION_REJECTED'))
  assert.ok(demoPresentations.some(record => record.status === 'failed' && record.failureCode === 'CREDENTIAL_REVOKED'))
  assert.ok(demoCredentials.some(record => record.attrs?.status === 'revoked' && record.attrs?.failureCode === 'CREDENTIAL_REVOKED'))
})
