import test from 'node:test'
import assert from 'node:assert/strict'

import { failureFromCode, failureHierarchy, normalizeVerificationRecord } from '../dva-dashboard/src/failures/failureModel.js'

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
