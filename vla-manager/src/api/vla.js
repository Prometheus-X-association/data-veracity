// A VLA is an ODCS data contract: its requirements are the `quality`
// entries of its schema objects – where DVA Processing reads them during
// attestation – and its free-text description is the contract's `purpose`.

// Every requirement, in the order the VLA Manager evaluates them.
export function vlaRequirements (vla) {
  return (vla?.schema || []).flatMap((schemaObject) => schemaObject?.quality || [])
}

export function vlaPurpose (vla) {
  return vla?.description?.purpose || ''
}

// The body of `POST /vla/from-templates`: the service adds the rendered
// requirements to the first schema object, the one describing the data.
export function vlaFromTemplatesBody ({ name, description, qualityTemplates }) {
  const purpose = (description || '').trim()
  return {
    name: name.trim(),
    // Optional, so left out rather than sent empty.
    ...(purpose ? { description: { purpose } } : {}),
    schema: [{
      name: 'data',
      logicalType: 'object',
      properties: [
        { name: 'timestamp', logicalType: 'string' },
        { name: 'result', logicalType: 'integer' }
      ]
    }],
    qualityTemplates
  }
}

// A requirement's implementation as readable text: jq arrives as a string, a
// JSON schema as an object or as JSON text, which is shown indented.
export function requirementImplementation (requirement) {
  const implementation = requirement?.implementation
  if (implementation === undefined || implementation === null || implementation === '') return ''
  if (typeof implementation !== 'string') return JSON.stringify(implementation, null, 2)
  try {
    const parsed = JSON.parse(implementation)
    if (parsed !== null && typeof parsed === 'object') return JSON.stringify(parsed, null, 2)
  } catch { /* not JSON: a jq program or an expectation, shown as written */ }
  return implementation
}

// The schema objects of a VLA – the data the contract describes – with their
// properties and requirements, for a read-only view.
export function vlaSchemaObjects (vla) {
  return (vla?.schema || []).map((schemaObject) => ({
    name: schemaObject?.name || 'Unnamed',
    logicalType: schemaObject?.logicalType || '',
    properties: (schemaObject?.properties || []).map((property) => ({
      name: property?.name ?? property?.schemaElement?.name ?? '',
      logicalType: property?.logicalType || '',
      required: property?.required === true
    })),
    requirements: schemaObject?.quality || []
  }))
}
