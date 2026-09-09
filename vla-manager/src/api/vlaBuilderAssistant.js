const MAX_SAMPLE_BYTES = 32 * 1024
const METADATA_FIELDS = ['name', 'description', 'dataReference', 'participants', 'tags']

function clone (value) {
  if (value === undefined) return undefined
  return JSON.parse(JSON.stringify(value))
}

function serialisedSize (value) {
  return new TextEncoder().encode(JSON.stringify(value)).length
}

export function createBuilderAssistantContext ({ metadata = {}, sampleData = null, selectedPath = null, fragments = [] } = {}) {
  let boundedSample = clone(sampleData)
  if (boundedSample !== null && serialisedSize(boundedSample) > MAX_SAMPLE_BYTES) {
    const json = JSON.stringify(boundedSample)
    const bytes = new TextEncoder().encode(json).slice(0, MAX_SAMPLE_BYTES)
    boundedSample = {
      truncated: true,
      preview: new TextDecoder().decode(bytes)
    }
  }
  return {
    metadata: clone(metadata) || {},
    sampleData: boundedSample,
    selectedPath: selectedPath || null,
    fragments: (fragments || []).map(fragment => ({
      data: clone(fragment.data) || {},
      requirement: fragment.requirement
        ? { id: fragment.requirement.id, name: fragment.requirement.name }
        : undefined
    }))
  }
}

function requiredVariables (template) {
  const schema = template?.evaluationMethod?.variableSchema || {}
  return Array.isArray(schema.required) ? schema.required : []
}

function hasValue (value) {
  return value !== undefined && value !== null && value !== ''
}

export function normaliseVlaAssistantReply (reply = {}, templates = []) {
  const byId = new Map((templates || []).map(template => [String(template.id), template]))
  const missingTemplates = Array.isArray(reply.missingTemplates) ? clone(reply.missingTemplates) : []
  const requirements = Array.isArray(reply.requirements) ? reply.requirements : []
  const matched = []
  for (const requirement of requirements) {
    const template = byId.get(String(requirement?.templateId || ''))
    if (!template) {
      missingTemplates.push({
        templateId: requirement?.templateId,
        reason: 'This template is no longer available.'
      })
      continue
    }
    matched.push({
      templateId: String(template.id),
      template,
      model: clone(requirement.model) || {},
      reason: String(requirement.reason || 'Selected for this requirement.')
    })
  }
  return {
    message: String(reply.message || ''),
    metadata: reply.metadata && typeof reply.metadata === 'object' ? clone(reply.metadata) : {},
    requirements: matched,
    missingTemplates
  }
}

function duplicateKey (templateId, model) {
  return `${templateId}:${JSON.stringify(model)}`
}

export function applyVlaAssistantDraft (state, draft, templates = []) {
  const current = state || { metadata: {}, fragments: [] }
  const available = new Map((templates || []).map(template => [String(template.id), template]))
  const requirements = Array.isArray(draft?.requirements) ? draft.requirements : []
  const prepared = []
  const seen = new Set((current.fragments || []).map(fragment => duplicateKey(fragment?.data?.id, fragment?.data?.model || {})))

  for (const requirement of requirements) {
    const template = available.get(String(requirement?.templateId || ''))
    if (!template) throw new Error('A selected template is no longer available.')
    const model = clone(requirement.model) || {}
    const missing = requiredVariables(template).filter(name => !hasValue(model[name]))
    if (missing.length) {
      throw new Error(`${template.name || 'The selected template'} is missing: ${missing.join(', ')}.`)
    }
    const key = duplicateKey(template.id, model)
    if (seen.has(key)) continue
    seen.add(key)
    prepared.push({
      data: { id: template.id, model },
      requirement: template,
      reason: String(requirement.reason || '')
    })
  }

  const metadata = { ...(clone(current.metadata) || {}) }
  for (const field of METADATA_FIELDS) {
    const value = draft?.metadata?.[field]
    if (hasValue(value) && (!Array.isArray(value) || value.length > 0)) metadata[field] = clone(value)
  }
  return {
    metadata,
    fragments: [...(clone(current.fragments) || []), ...prepared]
  }
}

export { MAX_SAMPLE_BYTES }
