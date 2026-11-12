import test from 'node:test'
import assert from 'node:assert/strict'

import { requirementImplementation, vlaFromTemplatesBody, vlaPurpose, vlaRequirements, vlaSchemaObjects } from '../src/api/vla.js'

test('reads the requirements of every schema object, in order', () => {
  const vla = {
    schema: [
      { name: 'data', quality: [{ engine: 'JQ' }, { engine: 'SCHEMA' }] },
      { name: 'no requirements' },
      { name: 'other', quality: [{ engine: 'GREAT_EXPECTATIONS' }] }
    ]
  }

  assert.deepEqual(vlaRequirements(vla).map((q) => q.engine), ['JQ', 'SCHEMA', 'GREAT_EXPECTATIONS'])
  assert.deepEqual(vlaRequirements({}), [])
})

test('reads the description as the contract purpose', () => {
  assert.equal(vlaPurpose({ description: { purpose: 'Asserts the year.' } }), 'Asserts the year.')
  assert.equal(vlaPurpose({}), '')
})

test('builds an ODCS VLA body, leaving an empty description out', () => {
  const templates = [{ id: 't-1', model: { year: 2026 } }]

  const body = vlaFromTemplatesBody({ name: ' Year check ', description: ' Checks the year. ', qualityTemplates: templates })

  assert.equal(body.name, 'Year check')
  assert.deepEqual(body.description, { purpose: 'Checks the year.' })
  assert.ok(Array.isArray(body.schema))
  assert.equal(body.schema[0].name, 'data')
  assert.equal(body.quality, undefined)
  assert.deepEqual(body.qualityTemplates, templates)

  assert.equal('description' in vlaFromTemplatesBody({ name: 'x', description: '  ', qualityTemplates: [] }), false)
})

test('shows an implementation as readable text, indenting JSON', () => {
  assert.equal(requirementImplementation({ implementation: '{ success: .a > 1 }' }), '{ success: .a > 1 }')
  assert.equal(requirementImplementation({ implementation: '{"type":"object"}' }), '{\n  "type": "object"\n}')
  assert.equal(requirementImplementation({ implementation: { type: 'object' } }), '{\n  "type": "object"\n}')
  assert.equal(requirementImplementation({}), '')
  assert.equal(requirementImplementation(undefined), '')
})

test('lists the schema objects of a VLA with their properties and requirements', () => {
  const vla = {
    schema: [{
      name: 'data',
      logicalType: 'object',
      properties: [
        { name: 'timestamp', logicalType: 'string' },
        { schemaElement: { name: 'result' }, logicalType: 'integer', required: true }
      ],
      quality: [{ engine: 'JQ' }]
    }, {}]
  }

  const [data, unnamed] = vlaSchemaObjects(vla)
  assert.deepEqual(data.properties, [
    { name: 'timestamp', logicalType: 'string', required: false },
    { name: 'result', logicalType: 'integer', required: true }
  ])
  assert.equal(data.requirements.length, 1)
  assert.equal(unnamed.name, 'Unnamed')
  assert.deepEqual(unnamed.properties, [])
  assert.deepEqual(vlaSchemaObjects(null), [])
})
