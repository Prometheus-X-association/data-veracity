import { validateTemplate, validationFailureFromError } from './templates.js'

const MAX_SAMPLE_BYTES = 32 * 1024
const METADATA_FIELDS = ['name', 'description', 'dataReference', 'participants', 'tags']

function clone (value) {
  if (value === undefined) return undefined
  return JSON.parse(JSON.stringify(value))
}

function serialisedSize (value) {
  return new TextEncoder().encode(JSON.stringify(value)).length
}

// What the assistant needs of its previous draft to complete it on a
// recheck: the chosen templates with their values, and what was missing.
function compactDraft (draft) {
  if (!draft) return null
  return {
    requirements: (draft.requirements || []).map(requirement => ({
      templateId: requirement.templateId,
      model: clone(requirement.model) || {},
      reason: requirement.reason
    })),
    missingTemplates: clone(draft.missingTemplates) || []
  }
}

export function createBuilderAssistantContext ({ metadata = {}, sampleData = null, selectedPath = null, fragments = [], draft = null } = {}) {
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
    })),
    draft: compactDraft(draft)
  }
}

// A missing template is named by the assistant; older replies only carry a
// reason, so its first sentence stands in as the name.
export function missingTemplateName (item = {}) {
  if (item.name && String(item.name).trim()) return String(item.name).trim()
  const reason = String(item.reason || item.description || '').trim()
  const sentence = reason.split(/(?<=[.!?])\s/)[0]
  return sentence.length > 60 ? `${sentence.slice(0, 57)}…` : sentence || 'Missing template'
}

// The request a template sub-session starts from: this one template only.
export function missingTemplateBrief (item = {}) {
  const name = missingTemplateName(item)
  const reason = String(item.reason || item.description || '').trim()
  return reason && reason !== name ? `${name}: ${reason}` : name
}

// Sent when the author has created templates and wants the draft completed.
export function recheckRequest (createdItems = []) {
  const names = createdItems.map(missingTemplateName)
  const list = names.map(name => `- ${name}`).join('\n')
  return `I have now created ${names.length === 1 ? 'this template' : 'these templates'}:\n${list}\nPlease check the catalog again and complete the draft.`
}

function requiredVariables (template) {
  const schema = template?.evaluationMethod?.variableSchema || {}
  return Array.isArray(schema.required) ? schema.required : []
}

function hasValue (value) {
  return value !== undefined && value !== null && value !== ''
}

export function normaliseAssistantRequest (value) {
  return typeof value === 'string' ? value.trim() : ''
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

// Each requirement goes through `/template/{id}/validate`, exactly as the
// requirement modal checks one before attaching it. A request that fails
// outright reads as the service being unavailable, never as a pass.
export async function checkDraftRequirements (requirements = [], validate = validateTemplate) {
  return Promise.all((requirements || []).map(async requirement => {
    try {
      return await validate(requirement.templateId, requirement.model)
    } catch (error) {
      return validationFailureFromError(error)
    }
  }))
}

export function passingRequirements (requirements = [], checks = []) {
  return (requirements || []).filter((_, index) => checks[index]?.valid === true)
}

const LIST_FIELDS = new Set(['participants', 'tags'])

function listValue (value) {
  const items = Array.isArray(value) ? value : String(value).split(',')
  return items.map(item => String(item).trim()).filter(Boolean)
}

// Participants and tags are added to, never replaced, matching the builder's
// own inputs, which ignore case when deciding whether an entry is new.
function mergeList (existing = [], additions = []) {
  const merged = [...existing]
  for (const item of additions) {
    if (!merged.some(present => present.toLowerCase() === item.toLowerCase())) merged.push(item)
  }
  return merged
}

export function applyVlaAssistantDraft (state, draft, templates = [], { includeMetadata = false } = {}) {
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
  for (const field of includeMetadata ? METADATA_FIELDS : []) {
    const value = draft?.metadata?.[field]
    if (!hasValue(value)) continue
    if (LIST_FIELDS.has(field)) {
      metadata[field] = mergeList(metadata[field] || [], listValue(value))
    } else if (typeof value === 'string' && value.trim()) {
      metadata[field] = value.trim()
    }
  }
  return {
    metadata,
    fragments: [...(clone(current.fragments) || []), ...prepared]
  }
}

export { MAX_SAMPLE_BYTES }
