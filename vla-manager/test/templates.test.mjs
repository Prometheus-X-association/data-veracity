import test from 'node:test'
import assert from 'node:assert/strict'

import {
  coerceTemplateValue,
  validateTemplate,
  validationFailureFromError,
  validationTone
} from '../src/api/templates.js'

test('validates a template through the VLA Manager API', async () => {
  const calls = []
  const client = {
    async post (url, body) {
      calls.push({ url, body })
      return { data: { valid: true, engine: 'JQ', implementation: '.foo == 1' } }
    }
  }

  const result = await validateTemplate('template/id', { minimum: 2 }, client)

  assert.deepEqual(calls, [{
    url: '/api/template/template%2Fid/validate',
    body: { minimum: 2 }
  }])
  assert.equal(result.valid, true)
})

test('uses different feedback tones for invalid and unavailable validation', () => {
  assert.equal(validationTone({ valid: false, reason: 'INVALID_IMPLEMENTATION' }), 'invalid')
  assert.equal(validationTone({ valid: false, reason: 'UNAVAILABLE_ENGINE' }), 'unavailable')
  assert.equal(validationTone({ valid: true }), 'valid')
})

test('coerces template inputs to their declared JSON schema type', () => {
  assert.equal(coerceTemplateValue('integer', '2'), 2)
  assert.equal(coerceTemplateValue('number', '2.5'), 2.5)
  assert.equal(coerceTemplateValue('boolean', 'true'), true)
  assert.equal(coerceTemplateValue('string', '2'), '2')
})

test('leaves a number input that will not convert as it was typed', () => {
  // NaN would serialise to null and be reported as the wrong type rather
  // than as the missing or malformed number it is.
  assert.equal(coerceTemplateValue('integer', ''), '')
  assert.equal(coerceTemplateValue('integer', '   '), '   ')
  assert.equal(coerceTemplateValue('number', 'abc'), 'abc')
  assert.equal(coerceTemplateValue('integer', '0'), 0)
})

test('keeps service failures separate from invalid evaluation logic', () => {
  const result = validationFailureFromError({
    message: 'Network Error',
    response: { data: { title: 'VLA Manager API is unreachable' } }
  })

  assert.equal(result.valid, false)
  assert.equal(result.reason, 'UNAVAILABLE_ENGINE')
})
