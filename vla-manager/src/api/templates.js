import axios from 'axios'

export async function validateTemplate (id, model, client = axios) {
  const response = await client.post(
    `/api/template/${encodeURIComponent(id)}/validate`,
    { model }
  )
  return response.data
}

export function validationTone (result) {
  if (result?.status === 'VALID') return 'valid'
  if (result?.status === 'UNAVAILABLE') return 'unavailable'
  return 'invalid'
}

export function coerceTemplateValue (type, value) {
  if (type === 'integer') return Number.parseInt(value, 10)
  if (type === 'number') return Number(value)
  if (type === 'boolean') return value === true || value === 'true'
  return value
}

export function validationFailureFromError (error) {
  return {
    valid: false,
    status: 'UNAVAILABLE',
    code: 'EVALUATION_ENGINE_UNAVAILABLE',
    message: 'The evaluation service is unavailable.',
    details: error?.response?.data?.title || error?.message || 'No details were returned.'
  }
}
