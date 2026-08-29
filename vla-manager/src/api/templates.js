import axios from 'axios'

export async function validateTemplate (id, model, client = axios) {
  const response = await client.post(
    `/api/template/${encodeURIComponent(id)}/validate`,
    { model }
  )
  return response.data
}

export function validationTone (result) {
  if (result?.valid) return 'valid'
  if (result?.reason === 'UNAVAILABLE_ENGINE') return 'unavailable'
  return 'invalid'
}

// Inputs hand back strings, so a value is coerced to the type its
// `variableSchema` declares before it is rendered into the template.
// Anything that will not convert stays as it was typed: NaN serialises to
// null, which the schema then rejects as the wrong type rather than as the
// missing or malformed number it actually is.
export function coerceTemplateValue (type, value) {
  if (type === 'integer' || type === 'number') {
    const number = type === 'integer' ? Number.parseInt(value, 10) : Number(value)
    return String(value).trim() === '' || Number.isNaN(number) ? value : number
  }
  if (type === 'boolean') return value === true || value === 'true'
  return value
}

export function validationFailureFromError (error) {
  return {
    valid: false,
    reason: 'UNAVAILABLE_ENGINE',
    details: `The evaluation service is unavailable.\n${error?.response?.data?.title || error?.message}`,
  }
}
