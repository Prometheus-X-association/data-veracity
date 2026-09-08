import test from 'node:test'
import assert from 'node:assert/strict'

import { applyTemplateProposal, assistantErrorMessage } from '../vla-manager/src/api/assistant.js'

test('applies only template fields from an assistant proposal', () => {
  const current = {
    id: 'template-1',
    name: 'Existing template',
    description: 'Keep this draft safe',
    criterionType: 'VALID_INVALID',
    targetAspect: 'SYNTAX',
    evaluationMethod: {
      engine: 'JQ',
      variableSchema: { type: 'object', properties: {}, required: [] },
      implementationTemplate: '.ok'
    }
  }

  const result = applyTemplateProposal(current, {
    name: 'xAPI schema',
    description: 'Checks xAPI data.',
    criterionType: 'VALID_INVALID',
    targetAspect: 'SYNTAX',
    evaluationMethod: {
      engine: 'SCHEMA',
      variableSchema: { type: 'object', properties: {}, required: [] },
      implementationTemplate: '{"type":"object"}'
    },
    id: 'must-not-replace'
  })

  assert.equal(result.id, 'template-1')
  assert.equal(result.name, 'xAPI schema')
  assert.equal(result.evaluationMethod.engine, 'SCHEMA')
})

test('does not replace a template when the assistant has no proposal', () => {
  const current = { name: 'Draft', evaluationMethod: { engine: 'JQ' } }

  assert.deepEqual(applyTemplateProposal(current, null), current)
})

test('uses RFC problem detail fields for assistant errors', () => {
  assert.equal(
    assistantErrorMessage({ response: { data: { detail: 'Model is unavailable.' } } }),
    'Model is unavailable.'
  )
  assert.equal(assistantErrorMessage({ message: 'Network failed' }), 'Network failed')
})
