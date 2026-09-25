import test from 'node:test'
import assert from 'node:assert/strict'

import { vlaFromTemplatesBody, vlaPurpose, vlaRequirements } from '../src/api/vla.js'

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
