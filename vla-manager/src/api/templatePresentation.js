// How templates are described to people: which quality engine a template
// runs on, and which variables it takes, instead of raw codes and JSON.

const ENGINES = {
  SCHEMA: {
    label: 'JSON Schema',
    summary: 'Checks that each record matches a JSON Schema document.'
  },
  JQ: {
    label: 'jq',
    summary: 'Runs a jq expression over the data that reports success or failure.'
  },
  GREAT_EXPECTATIONS: {
    label: 'Great Expectations',
    summary: 'Treats the data as a table and checks it with a Great Expectations expectation.'
  }
}

export function engineInfo (engine) {
  return ENGINES[engine] || { label: engine || 'No engine', summary: '' }
}

// The same names the template editor offers when a variable is defined.
const TYPE_LABELS = {
  string: 'Text',
  number: 'Number',
  integer: 'Integer',
  boolean: 'Boolean',
  object: 'JSON object',
  array: 'List',
  null: 'Empty'
}

function typeLabel (definition = {}) {
  if (Array.isArray(definition.enum) && definition.enum.length) {
    return `One of ${definition.enum.map(value => JSON.stringify(value)).join(', ')}`
  }
  if (definition.const !== undefined) return `Exactly ${JSON.stringify(definition.const)}`
  const types = Array.isArray(definition.type) ? definition.type : [definition.type].filter(Boolean)
  if (!types.length) return 'Any value'
  return types.map(type => {
    let label = TYPE_LABELS[type] || type
    if (type === 'array' && definition.items?.type && !Array.isArray(definition.items.type)) {
      label = `List of ${(TYPE_LABELS[definition.items.type] || definition.items.type).toLowerCase()}`
    }
    if (type === 'string' && definition.format) label = `${label} (${definition.format})`
    return label
  }).join(' or ')
}

function constraints (definition = {}) {
  const notes = []
  if (definition.minimum !== undefined) notes.push(`at least ${definition.minimum}`)
  if (definition.exclusiveMinimum !== undefined) notes.push(`more than ${definition.exclusiveMinimum}`)
  if (definition.maximum !== undefined) notes.push(`at most ${definition.maximum}`)
  if (definition.exclusiveMaximum !== undefined) notes.push(`less than ${definition.exclusiveMaximum}`)
  if (definition.minLength !== undefined) notes.push(`at least ${definition.minLength} characters`)
  if (definition.maxLength !== undefined) notes.push(`at most ${definition.maxLength} characters`)
  if (definition.pattern) notes.push(`matches ${definition.pattern}`)
  if (definition.default !== undefined) notes.push(`defaults to ${JSON.stringify(definition.default)}`)
  const fields = definition.properties ? Object.keys(definition.properties) : []
  if (fields.length) notes.push(`fields: ${fields.join(', ')}`)
  return notes.join('; ')
}

// Most templates use the JSON Schema shape {type: 'object', properties, required},
// but older ones map variable names straight to their definitions.
function variableDefinitions (schema) {
  if (!schema || typeof schema !== 'object') return {}
  if (schema.properties && typeof schema.properties === 'object') return schema.properties
  if (schema.type) return {}
  const entries = Object.entries(schema)
  const flat = entries.length && entries.every(([, value]) => value && typeof value === 'object' && !Array.isArray(value))
  return flat ? schema : {}
}

export function describeVariables (schema) {
  const required = new Set(Array.isArray(schema?.required) ? schema.required : [])
  return Object.entries(variableDefinitions(schema)).map(([name, definition]) => ({
    name,
    type: typeLabel(definition || {}),
    required: required.has(name),
    description: definition?.description || definition?.title || '',
    constraints: constraints(definition || {})
  }))
}

// How much of the test data a bug report quotes.
const REPORTED_DATA_CHARS = 1500

// The message that opens the template assistant after a failed test, for the
// author to adjust and send: what was run, on what, and what came of it.
export function templateBugReport ({ model = {}, data, outcome = {} } = {}) {
  let quoted = JSON.stringify(data ?? null)
  if (quoted.length > REPORTED_DATA_CHARS) quoted = `${quoted.slice(0, REPORTED_DATA_CHARS)}… (truncated)`
  const result = outcome.tone === 'error'
    ? `It could not be evaluated: ${outcome.message || 'no error message'}`
    : `It reported that the data does not satisfy it${outcome.message ? ` (details: ${outcome.message})` : ''}, which I believe is wrong.`
  return [
    'Testing this template gave a wrong result.',
    `Template variables: ${JSON.stringify(model)}`,
    `Test data: ${quoted}`,
    `Result: ${result}`,
    'Please find the cause in the implementation template and fix it.'
  ].join('\n')
}
