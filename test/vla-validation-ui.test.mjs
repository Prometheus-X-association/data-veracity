import test from 'node:test'
import assert from 'node:assert/strict'

import {
  coerceTemplateValue,
  validateTemplate,
  validationTone
} from '../vla-manager/src/api/templates.js'

test('validates a template through the VLA Manager API', async () => {
  const calls = []
  const client = {
    async post (url, body) {
      calls.push({ url, body })
      return { data: { valid: true, status: 'VALID', code: 'EVALUATION_LOGIC_VALID' } }
    }
  }

  const result = await validateTemplate('template/id', { minimum: 2 }, client)

  assert.deepEqual(calls, [{
    url: '/api/template/template%2Fid/validate',
    body: { model: { minimum: 2 } }
  }])
  assert.equal(result.valid, true)
})

test('uses different feedback tones for invalid and unavailable validation', () => {
  assert.equal(validationTone({ status: 'INVALID' }), 'invalid')
  assert.equal(validationTone({ status: 'UNAVAILABLE' }), 'unavailable')
  assert.equal(validationTone({ status: 'VALID' }), 'valid')
})

test('coerces template inputs to their declared JSON schema type', () => {
  assert.equal(coerceTemplateValue('integer', '2'), 2)
  assert.equal(coerceTemplateValue('number', '2.5'), 2.5)
  assert.equal(coerceTemplateValue('boolean', 'true'), true)
  assert.equal(coerceTemplateValue('string', '2'), '2')
})
