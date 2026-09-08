export function renameTemplateVariable (schema, oldName, nextName) {
  const name = nextName.trim()
  const properties = schema.properties || {}
  if (!name || name === oldName || properties[oldName] === undefined || properties[name] !== undefined) return schema

  const nextProperties = { ...properties, [name]: properties[oldName] }
  delete nextProperties[oldName]
  return {
    ...schema,
    properties: nextProperties,
    required: (schema.required || []).map(item => item === oldName ? name : item)
  }
}

export function updateTemplateVariable (schema, name, patch) {
  return {
    ...schema,
    properties: {
      ...(schema.properties || {}),
      [name]: { ...((schema.properties || {})[name] || {}), ...patch }
    }
  }
}

export function removeTemplateVariable (schema, name) {
  const properties = { ...(schema.properties || {}) }
  delete properties[name]
  return {
    ...schema,
    properties,
    required: (schema.required || []).filter(item => item !== name)
  }
}

export function createVariableKeyStore () {
  const keys = new Map()
  let sequence = 0

  return {
    keyFor (name) {
      if (!keys.has(name)) keys.set(name, `variable-${++sequence}`)
      return keys.get(name)
    },
    rename (oldName, nextName) {
      const key = keys.get(oldName)
      if (key) {
        keys.delete(oldName)
        keys.set(nextName, key)
      }
    },
    remove (name) {
      keys.delete(name)
    }
  }
}
