import test from 'node:test'
import assert from 'node:assert/strict'

import { describeVariables, engineInfo, templateBugReport } from '../src/api/templatePresentation.js'

test('names each quality engine and says what it checks', () => {
  assert.equal(engineInfo('SCHEMA').label, 'JSON Schema')
  assert.equal(engineInfo('JQ').label, 'jq')
  assert.equal(engineInfo('GREAT_EXPECTATIONS').label, 'Great Expectations')
  assert.match(engineInfo('JQ').summary, /jq expression/)
  assert.deepEqual(engineInfo('NEW_ENGINE'), { label: 'NEW_ENGINE', summary: '' })
  assert.equal(engineInfo(undefined).label, 'No engine')
})

test('lists variables with readable types, required flags and constraints', () => {
  const rows = describeVariables({
    type: 'object',
    properties: {
      schema: { type: ['object', 'string'], description: 'The JSON Schema to check against' },
      max: { type: 'integer', minimum: 0, maximum: 100 },
      unit: { type: 'string', enum: ['kWh', 'MWh'] },
      tags: { type: 'array', items: { type: 'string' } },
      since: { type: 'string', format: 'date-time', default: '2025-01-01T00:00:00Z' },
      strict: { type: 'boolean' },
      anything: {}
    },
    required: ['schema', 'max']
  })

  assert.deepEqual(rows.map(row => [row.name, row.type, row.required]), [
    ['schema', 'JSON object or Text', true],
    ['max', 'Integer', true],
    ['unit', 'One of "kWh", "MWh"', false],
    ['tags', 'List of text', false],
    ['since', 'Text (date-time)', false],
    ['strict', 'Boolean', false],
    ['anything', 'Any value', false]
  ])
  assert.equal(rows[0].description, 'The JSON Schema to check against')
  assert.equal(rows[1].constraints, 'at least 0; at most 100')
  assert.equal(rows[4].constraints, 'defaults to "2025-01-01T00:00:00Z"')
})

test('reads older schemas that map variable names straight to definitions', () => {
  const rows = describeVariables({ value: { type: 'string' }, limit: { type: 'number' } })

  assert.deepEqual(rows.map(row => [row.name, row.type]), [['value', 'Text'], ['limit', 'Number']])
})

test('has nothing to list for an empty or missing schema', () => {
  assert.deepEqual(describeVariables(null), [])
  assert.deepEqual(describeVariables({ type: 'object' }), [])
  assert.deepEqual(describeVariables({ type: 'object', properties: {} }), [])
})

test('reports a failed template test for the assistant to fix', () => {
  const report = templateBugReport({
    model: { fields: ['foo'], minRequired: 1 },
    data: { foo: 1 },
    outcome: { tone: 'error', message: 'Cannot check whether number has a string key' }
  })

  assert.equal(report, [
    'Testing this template gave a wrong result.',
    'Template variables: {"fields":["foo"],"minRequired":1}',
    'Test data: {"foo":1}',
    'Result: It could not be evaluated: Cannot check whether number has a string key',
    'Please find the cause in the implementation template and fix it.'
  ].join('\n'))
})

test('reports a wrong verdict and truncates large test data', () => {
  const report = templateBugReport({
    model: {},
    data: { text: 'x'.repeat(5000) },
    outcome: { tone: 'failed', message: 'value is empty' }
  })

  assert.match(report, /Result: It reported that the data does not satisfy it \(details: value is empty\), which I believe is wrong\./)
  assert.match(report, /… \(truncated\)\n/)
  assert.ok(report.length < 2000)
})
