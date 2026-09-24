import { validateTemplate, validationFailureFromError } from './templates.js'

const MAX_SAMPLE_BYTES = 32 * 1024
const METADATA_FIELDS = ['name', 'description']

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

// JSON with object keys sorted, so the same model compares equal however
// the assistant happened to order its keys.
function canonical (value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value ?? null)
}

// A requirement is its template together with the values filled into it.
function duplicateKey (templateId, model) {
  return `${templateId}:${canonical(model || {})}`
}

const fragmentKey = fragment => duplicateKey(fragment?.data?.id, fragment?.data?.model)
const requirementKey = requirement => duplicateKey(requirement?.templateId, requirement?.model)

// How applying a draft changes the requirements already in the builder: the
// draft is the complete list, so attached requirements it leaves out are
// removed.
export function planDraftChanges (fragments = [], requirements = []) {
  const attached = new Set((fragments || []).map(fragmentKey))
  const drafted = new Set((requirements || []).map(requirementKey))
  return {
    keep: (requirements || []).filter(requirement => attached.has(requirementKey(requirement))),
    add: (requirements || []).filter(requirement => !attached.has(requirementKey(requirement))),
    remove: (fragments || []).filter(fragment => !drafted.has(fragmentKey(fragment)))
  }
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

// With `replaceRequirements`, the draft's requirements become the builder's
// requirements: attached ones it lists are kept as they are, the others are
// added, and attached ones it leaves out are removed. Otherwise they are
// only added.
export function applyVlaAssistantDraft (state, draft, templates = [], { includeMetadata = false, replaceRequirements = false } = {}) {
  const current = state || { metadata: {}, fragments: [] }
  const available = new Map((templates || []).map(template => [String(template.id), template]))
  const requirements = Array.isArray(draft?.requirements) ? draft.requirements : []
  const attached = new Map((current.fragments || []).map(fragment => [fragmentKey(fragment), fragment]))
  const prepared = []
  const seen = new Set(replaceRequirements ? [] : attached.keys())

  for (const requirement of requirements) {
    const kept = replaceRequirements && attached.get(requirementKey(requirement))
    if (kept) {
      if (!seen.has(fragmentKey(kept))) prepared.push(clone(kept))
      seen.add(fragmentKey(kept))
      continue
    }
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
    if (typeof value === 'string' && value.trim()) metadata[field] = value.trim()
  }
  return {
    metadata,
    fragments: replaceRequirements ? prepared : [...(clone(current.fragments) || []), ...prepared]
  }
}

export { MAX_SAMPLE_BYTES }

// What the VLA builder requires before a VLA can be created; the
// description is optional. Mirrors the check on the "Create VLA" button.
export const REQUIRED_METADATA = [
  { field: 'name', label: 'Name' }
]

// The builder's metadata once the assistant's suggestion is applied to it.
export function mergedMetadata (builderMetadata = {}, draftMetadata = {}) {
  return applyVlaAssistantDraft(
    { metadata: builderMetadata || {}, fragments: [] },
    { metadata: draftMetadata || {}, requirements: [] },
    [],
    { includeMetadata: true }
  ).metadata
}

export function missingMetadata (metadata = {}) {
  return REQUIRED_METADATA.filter(({ field }) => {
    const value = metadata?.[field]
    return Array.isArray(value) ? value.length === 0 : !String(value ?? '').trim()
  })
}
