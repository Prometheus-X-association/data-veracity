import test from 'node:test'
import assert from 'node:assert/strict'

import {
  applyVlaAssistantDraft,
  createBuilderAssistantContext,
  normaliseAssistantRequest,
  normaliseVlaAssistantReply
} from '../vla-manager/src/api/vlaBuilderAssistant.js'

const schemaTemplate = {
  id: '11111111-1111-1111-1111-111111111111',
  name: 'JSON Schema',
  description: 'Checks the record shape.',
  criterionType: 'VALID_INVALID',
  targetAspect: 'SYNTAX',
  evaluationMethod: {
    engine: 'SCHEMA',
    variableSchema: {
      type: 'object',
      properties: { schema: { type: 'object' } },
      required: ['schema']
    },
    implementationTemplate: '{{ schema }}'
  }
}

test('bounds builder context and keeps the selected JSON path', () => {
  const context = createBuilderAssistantContext({
    metadata: { name: 'Energy' },
    sampleData: { value: 'x' },
    selectedPath: 'records[0].production_kwh',
    fragments: [{ data: { id: 'old', model: { property: 'value' } } }]
  })

  assert.equal(context.selectedPath, 'records[0].production_kwh')
  assert.deepEqual(context.metadata, { name: 'Energy' })
  assert.equal(context.fragments.length, 1)
  assert.deepEqual(context.sampleData, { value: 'x' })
})

test('accepts text requests and ignores browser events', () => {
  assert.equal(normaliseAssistantRequest('  Check the sample schema  '), 'Check the sample schema')
  assert.equal(normaliseAssistantRequest({ type: 'click', isTrusted: true }), '')
  assert.equal(normaliseAssistantRequest(undefined), '')
})

test('normalises a catalog-backed assistant reply', () => {
  const reply = normaliseVlaAssistantReply({
    message: 'I found a matching schema.',
    metadata: { name: 'Energy records' },
    requirements: [{ templateId: schemaTemplate.id, model: { schema: { type: 'object' } }, reason: 'Matches the sample.' }],
    missingTemplates: []
  }, [schemaTemplate])

  assert.equal(reply.requirements[0].template, schemaTemplate)
  assert.equal(reply.requirements[0].model.schema.type, 'object')
})

test('applies a draft atomically while preserving existing fragments', () => {
  const state = {
    metadata: { name: 'Existing', tags: ['existing'] },
    fragments: [{ data: { id: 'old', model: {} }, requirement: { name: 'Old' } }]
  }
  const draft = {
    metadata: { name: 'Generated', description: 'Checks the sample.' },
    requirements: [{ templateId: schemaTemplate.id, model: { schema: { type: 'object' } }, reason: 'Matches the sample.' }]
  }

  const next = applyVlaAssistantDraft(state, draft, [schemaTemplate])

  assert.equal(next.metadata.name, 'Generated')
  assert.equal(next.metadata.tags[0], 'existing')
  assert.equal(next.fragments.length, 2)
  assert.equal(next.fragments[1].data.id, schemaTemplate.id)
  assert.equal(next.fragments[1].requirement, schemaTemplate)
  assert.equal(state.fragments.length, 1)
})

test('rejects an unavailable or incomplete requirement before changing state', () => {
  const state = { metadata: { name: 'Existing' }, fragments: [] }
  assert.throws(() => applyVlaAssistantDraft(
    state,
    { metadata: { name: 'Draft' }, requirements: [{ templateId: 'missing', model: {} }] },
    []
  ), /template is no longer available/)
  assert.deepEqual(state, { metadata: { name: 'Existing' }, fragments: [] })
})
