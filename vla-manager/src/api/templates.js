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
  return request({ method: 'post', url: `/api/template/${encodeURIComponent(id)}/render`, data: { model } })
}

export function evaluateTemplate (templateID, templateModel, data) {
  return request({ method: 'post', url: '/api/evaluate/from-template', data: { templateID, templateModel, data } })
}

export { normaliseError }
