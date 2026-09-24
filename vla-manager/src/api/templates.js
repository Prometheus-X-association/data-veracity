import axios from 'axios'

function normaliseError (error) {
  const response = error?.response
  const body = response?.data || {}
  const message = body.details || body.detail || body.title || error?.message || 'The template service could not complete the request.'
  return {
    status: response?.status || 0,
    code: body.type || body.code || 'GATEWAY_UNAVAILABLE',
    message,
    details: body,
    retryable: !response || response.status >= 500 || response.status === 408 || response.status === 429
  }
}

async function request (config) {
  try {
    const response = await axios(config)
    return response.data
  } catch (error) {
    throw normaliseError(error)
  }
}

export function listTemplates () {
  return request({ method: 'get', url: '/api/template' })
}

export function getTemplate (id) {
  return request({ method: 'get', url: `/api/template/${encodeURIComponent(id)}` })
}

export function createTemplate (template) {
  return request({ method: 'post', url: '/api/template', data: template })
}

export function updateTemplate (id, template) {
  return request({ method: 'patch', url: `/api/template/${encodeURIComponent(id)}`, data: template })
}

export function deleteTemplate (id) {
  return request({ method: 'delete', url: `/api/template/${encodeURIComponent(id)}` })
}

export function renderTemplate (id, model) {
  // The body is the model itself (the spec's TemplateModel), not wrapped.
  return request({ method: 'post', url: `/api/template/${encodeURIComponent(id)}/render`, data: model })
}

export function evaluateTemplate (templateID, templateModel, data) {
  return request({ method: 'post', url: '/api/evaluate/from-template', data: { templateID, templateModel, data } })
}

export { normaliseError }

// Validation keeps the raw axios error rather than going through
// `request`: `validationFailureFromError` reads the untouched response so
// an unreachable service stays distinguishable from rejected logic, and
// the injectable `client` keeps the call testable without a stub axios.
export async function validateTemplate (id, model, client = axios) {
  const response = await client.post(
    `/api/template/${encodeURIComponent(id)}/validate`,
    // The body is the model itself (the spec's TemplateModel), not wrapped.
    model
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
