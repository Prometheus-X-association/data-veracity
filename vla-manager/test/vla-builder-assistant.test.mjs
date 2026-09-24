import test from 'node:test'
import assert from 'node:assert/strict'

import {
  applyVlaAssistantDraft,
  checkDraftRequirements,
  createBuilderAssistantContext,
  normaliseAssistantRequest,
  normaliseVlaAssistantReply,
  passingRequirements
} from '../src/api/vlaBuilderAssistant.js'

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

  const next = applyVlaAssistantDraft(state, draft, [schemaTemplate], { includeMetadata: true })

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

test('checks every draft requirement and treats a failed request as unavailable', async () => {
  const requirements = [
    { templateId: 'a', model: { max: 1 } },
    { templateId: 'b', model: { max: 'x' } },
    { templateId: 'c', model: {} }
  ]
  const calls = []
  const checks = await checkDraftRequirements(requirements, async (id, model) => {
    calls.push([id, model])
    if (id === 'c') throw new Error('network down')
    return id === 'a' ? { valid: true } : { valid: false, reason: 'INVALID_IMPLEMENTATION', details: 'not an integer' }
  })

  assert.deepEqual(calls, [['a', { max: 1 }], ['b', { max: 'x' }], ['c', {}]])
  assert.equal(checks[0].valid, true)
  assert.equal(checks[1].reason, 'INVALID_IMPLEMENTATION')
  assert.equal(checks[2].valid, false)
  assert.equal(checks[2].reason, 'UNAVAILABLE_ENGINE')
  assert.deepEqual(passingRequirements(requirements, checks), [requirements[0]])
})

test('leaves metadata alone unless it is opted in', () => {
  const state = { metadata: { name: 'Mine', tags: [] }, fragments: [] }
  const selection = { metadata: { name: 'Suggested' }, requirements: [] }

  assert.equal(applyVlaAssistantDraft(state, selection, []).metadata.name, 'Mine')
  assert.equal(
    applyVlaAssistantDraft(state, selection, [], { includeMetadata: true }).metadata.name,
    'Suggested'
  )
})

test('applies metadata on its own and merges participants and tags', () => {
  const state = {
    metadata: { name: '', participants: ['Alice'], tags: ['energy'] },
    fragments: [{ data: { id: 'old', model: {} }, requirement: { name: 'Old' } }]
  }
  const next = applyVlaAssistantDraft(
    state,
    { metadata: { name: ' Energy records ', participants: 'alice, Bob', tags: ['Energy', 'hourly'] }, requirements: [] },
    [],
    { includeMetadata: true }
  )

  assert.equal(next.metadata.name, 'Energy records')
  assert.deepEqual(next.metadata.participants, ['Alice', 'Bob'])
  assert.deepEqual(next.metadata.tags, ['energy', 'hourly'])
  assert.equal(next.fragments.length, 1)
})
