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
