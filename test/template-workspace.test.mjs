import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import { normaliseError } from '../vla-manager/src/api/templates.js'
import { normalizeEvaluationResult, failureFromCode } from '../vla-manager/src/failures/failureModel.js'

test('keeps the VLA failure model inside its Docker build context', () => {
  const source = fs.readFileSync(new URL('../vla-manager/src/failures/failureModel.js', import.meta.url), 'utf8')
  assert.doesNotMatch(source, /\.\.\/\.\.\/\.\.\/dva-dashboard/)
})

test('normalises a template validation response for inline guidance', () => {
  const error = normaliseError({
    response: {
      status: 400,
      data: { type: 'BAD_REQUEST', title: 'Template input is invalid', details: 'Name is required.' }
    }
  })

  assert.equal(error.status, 400)
  assert.equal(error.code, 'BAD_REQUEST')
  assert.equal(error.message, 'Name is required.')
  assert.equal(error.retryable, false)
})

test('keeps engine evidence when a template evaluation fails', () => {
  const failure = normalizeEvaluationResult({
    engine: 'JQ',
    success: false,
    details: 'customer_id is blank'
  }, { source: 'template-tester' })

  assert.equal(failure.code, 'JQ_CHECK_FAILED')
  assert.match(failure.evidence, /customer_id is blank/)
  assert.equal(failure.source, 'template-tester')
})

test('maps a missing template to a recoverable workspace failure', () => {
  const failure = failureFromCode('UNKNOWN_TEMPLATE', { evidence: 'Template was deleted.' })
  assert.equal(failure.status, 'unavailable')
  assert.equal(failure.retryable, true)
  assert.match(failure.nextAction, /Refresh/)
})
