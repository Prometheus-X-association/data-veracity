import axios from 'axios'
import { normaliseError } from './templates.js'

const TEMPLATE_FIELDS = ['name', 'description', 'criterionType', 'targetAspect', 'evaluationMethod']

export function applyTemplateProposal (current, proposal) {
  if (!proposal || typeof proposal !== 'object') return current
  const next = { ...current }
  for (const field of TEMPLATE_FIELDS) {
    if (proposal[field] !== undefined) next[field] = field === 'evaluationMethod'
      ? { ...proposal[field] }
      : proposal[field]
  }
  return next
}

export function assistantErrorMessage (error) {
  const body = error?.response?.data || {}
  return body.detail || body.title || error?.message || 'The template assistant is unavailable.'
}

export async function askTemplateAssistant (payload, client = axios) {
  try {
    const response = await client.post('/api/assistant/template', payload)
    return response.data
  } catch (error) {
    throw normaliseError(error)
  }
}
