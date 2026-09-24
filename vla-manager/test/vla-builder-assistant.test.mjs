import test from 'node:test'
import assert from 'node:assert/strict'

import {
  applyVlaAssistantDraft,
  checkDraftRequirements,
  missingTemplateBrief,
  missingTemplateName,
  mergedMetadata,
  missingMetadata,
  REQUIRED_METADATA,
  createBuilderAssistantContext,
  normaliseAssistantRequest,
  normaliseVlaAssistantReply,
  passingRequirements,
  planDraftChanges,
  recheckRequest
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

test('applies metadata on its own, keeping the existing requirements', () => {
  const state = {
    metadata: { name: '', description: 'Mine' },
    fragments: [{ data: { id: 'old', model: {} }, requirement: { name: 'Old' } }]
  }
  const next = applyVlaAssistantDraft(
    state,
    { metadata: { name: ' Energy records ', description: '  ', participants: ['ignored'] }, requirements: [] },
    [],
    { includeMetadata: true }
  )

  assert.deepEqual(next.metadata, { name: 'Energy records', description: 'Mine' })
  assert.equal(next.fragments.length, 1)
})
test('sends a compact copy of the previous draft with the builder context', () => {
  const draft = {
    message: 'Draft',
    requirements: [{ templateId: schemaTemplate.id, template: schemaTemplate, model: { schema: {} }, reason: 'Fits.' }],
    missingTemplates: [{ name: 'Freshness window', reason: 'At most 1h old.' }]
  }

  const context = createBuilderAssistantContext({ metadata: {}, draft })

  assert.deepEqual(context.draft, {
    requirements: [{ templateId: schemaTemplate.id, model: { schema: {} }, reason: 'Fits.' }],
    missingTemplates: [{ name: 'Freshness window', reason: 'At most 1h old.' }]
  })
  assert.equal(createBuilderAssistantContext({}).draft, null)
})

test('names a missing template and briefs a sub-session on that one template', () => {
  const named = { name: 'Freshness window', reason: 'Every record is at most one hour old.' }
  const unnamed = { reason: 'Values stay between 0 and 100. They are in kWh.' }

  assert.equal(missingTemplateName(named), 'Freshness window')
  assert.equal(missingTemplateName(unnamed), 'Values stay between 0 and 100.')
  assert.equal(missingTemplateName({}), 'Missing template')
  assert.equal(missingTemplateBrief(named), 'Freshness window: Every record is at most one hour old.')
  assert.equal(missingTemplateBrief({ name: 'Only a name' }), 'Only a name')
})

test('asks for a recheck naming the templates the author ticked', () => {
  const request = recheckRequest([{ name: 'Freshness window' }, { name: 'Production range' }])

  assert.match(request, /these templates:\n- Freshness window\n- Production range\n/)
  assert.match(request, /check the catalog again and complete the draft/)
  assert.match(recheckRequest([{ name: 'One' }]), /this template:\n- One\n/)
})

test('merges the suggested metadata into what the author entered', () => {
  assert.deepEqual(
    mergedMetadata({ name: 'Mine', description: '' }, { name: 'Suggested', description: 'Checks energy records.' }),
    { name: 'Suggested', description: 'Checks energy records.' }
  )
  assert.deepEqual(mergedMetadata({ name: 'Mine', description: 'Kept' }, { name: '' }), { name: 'Mine', description: 'Kept' })
})
test('requires only a name; the description is optional', () => {
  assert.deepEqual(REQUIRED_METADATA.map(item => item.field), ['name'])
  assert.deepEqual(missingMetadata({ name: ' ', description: 'd' }).map(gap => gap.field), ['name'])
  assert.deepEqual(missingMetadata({ name: 'VLA', description: '' }), [])
})

const rangeTemplate = {
  id: '22222222-2222-2222-2222-222222222222',
  name: 'Range',
  evaluationMethod: { engine: 'JQ', variableSchema: { type: 'object', required: ['max'] }, implementationTemplate: '.v <= {{{max}}}' }
}
const attachedSchema = { data: { id: schemaTemplate.id, model: { schema: { type: 'object', required: ['a'] } } }, requirement: schemaTemplate }
const attachedRange = { data: { id: rangeTemplate.id, model: { max: 3 } }, requirement: rangeTemplate }

test('plans which attached requirements a complete draft keeps, adds and removes', () => {
  const requirements = [
    // Same model as attached, keys in another order: still the same one.
    { templateId: schemaTemplate.id, model: { schema: { required: ['a'], type: 'object' } } },
    { templateId: rangeTemplate.id, model: { max: 5 } }
  ]

  const plan = planDraftChanges([attachedSchema, attachedRange], requirements)

  assert.deepEqual(plan.keep, [requirements[0]])
  assert.deepEqual(plan.add, [requirements[1]])
  assert.deepEqual(plan.remove, [attachedRange])
})

test('replaces the builder requirements with the draft, keeping attached ones as they are', () => {
  const state = { metadata: { name: 'VLA', description: '' }, fragments: [attachedSchema, attachedRange] }
  const draft = {
    requirements: [
      { templateId: schemaTemplate.id, model: { schema: { required: ['a'], type: 'object' } } },
      { templateId: rangeTemplate.id, model: { max: 5 }, reason: 'Raised the limit.' },
      { templateId: rangeTemplate.id, model: { max: 5 } }
    ]
  }

  // The schema template is no longer in the catalog: a kept requirement
  // stays without being looked up again.
  const next = applyVlaAssistantDraft(state, draft, [rangeTemplate], { replaceRequirements: true })

  assert.equal(next.fragments.length, 2)
  assert.deepEqual(next.fragments[0], attachedSchema)
  assert.deepEqual(next.fragments[1].data, { id: rangeTemplate.id, model: { max: 5 } })
  assert.deepEqual(state.fragments, [attachedSchema, attachedRange])
})

test('an empty complete draft removes every attached requirement', () => {
  const next = applyVlaAssistantDraft(
    { metadata: {}, fragments: [attachedSchema] },
    { requirements: [] },
    [],
    { replaceRequirements: true }
  )

  assert.deepEqual(next.fragments, [])
})
