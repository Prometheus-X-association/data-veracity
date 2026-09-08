import test from 'node:test'
import assert from 'node:assert/strict'

import { applyTemplateProposal, assistantErrorMessage } from '../vla-manager/src/api/assistant.js'
import {
  formatAssistantJson,
  normaliseAssistantExamples,
  tokeniseAssistantJson
} from '../vla-manager/src/api/assistantPresentation.js'
import { createVariableKeyStore, renameTemplateVariable } from '../vla-manager/src/api/templateVariables.js'

test('renames one template variable without disturbing siblings or focus identity', () => {
  const schema = {
    type: 'object',
    properties: {
      first: { type: 'string', description: 'First value' },
      second: { type: 'number', description: 'Second value' }
    },
    required: ['first', 'second']
  }
  const keys = createVariableKeyStore()
  const firstKey = keys.keyFor('first')
  const secondKey = keys.keyFor('second')

  const next = renameTemplateVariable(schema, 'first', 'firs')
  keys.rename('first', 'firs')

  assert.deepEqual(next.properties, {
    firs: { type: 'string', description: 'First value' },
    second: { type: 'number', description: 'Second value' }
  })
  assert.deepEqual(next.required, ['firs', 'second'])
  assert.deepEqual(schema.properties, {
    first: { type: 'string', description: 'First value' },
    second: { type: 'number', description: 'Second value' }
  })
  assert.equal(keys.keyFor('firs'), firstKey)
  assert.equal(keys.keyFor('second'), secondKey)
})

test('normalises assistant examples into passing and failing lists', () => {
  assert.deepEqual(
    normaliseAssistantExamples({
      passing: { timestamp: '2026-09-08T08:00:00Z', production_kwh: 420 },
      failing: [
        { timestamp: 'not-a-date' },
        { timestamp: '2026-09-08T08:00:00Z', production_kwh: -2 }
      ]
    }),
    {
      passing: [{ timestamp: '2026-09-08T08:00:00Z', production_kwh: 420 }],
      failing: [
        { timestamp: 'not-a-date' },
        { timestamp: '2026-09-08T08:00:00Z', production_kwh: -2 }
      ]
    }
  )
})

test('formats assistant JSON without losing primitive values', () => {
  assert.equal(formatAssistantJson({ valid: true, count: 2 }), '{\n  "valid": true,\n  "count": 2\n}')
  assert.equal(formatAssistantJson('not available'), 'not available')
})

test('tokenises JSON for readable syntax colouring', () => {
  const tokens = tokeniseAssistantJson({ valid: true, count: 2, label: 'ok' })

  assert.ok(tokens.some(token => token.type === 'key' && token.text === '"valid"'))
  assert.ok(tokens.some(token => token.type === 'boolean' && token.text === 'true'))
  assert.ok(tokens.some(token => token.type === 'number' && token.text === '2'))
  assert.ok(tokens.some(token => token.type === 'string' && token.text === '"ok"'))
})

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
