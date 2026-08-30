import { http, HttpResponse } from 'msw'
import { v4 as uuid } from 'uuid'
import { renderTemplate } from './templates'
import { responseForFixture, templateFailureFixtures } from './failureFixtures'

const vlas = [
  {
    id: uuid(),
    name: 'Customer events quality',
    description: 'Mocked VLA one',
    participants: ['analytics-team', 'customer-data-provider'],
    dataReference: 'customer-events',
    tags: ['freshness', 'schema'],
    quality: [
      {
        engine: 'JQ',
        implementation: '.foo == .bar'
      }
    ]
  },
  {
    id: uuid(),
    name: 'Learning record quality',
    description: 'Mocked VLA two',
    participants: ['learning-platform'],
    dataReference: 'xapi-statements',
    tags: ['accuracy'],
    quality: [
      {
        engine: 'GREAT_EXPECTATIONS',
        implementation: '... great expectations yaml ...'
      }
    ]
  }
]

let templates = [
  {
    id: uuid(),
    name: 'JSON schema (mock)',
    description: 'Mock template for JSON schema compliance',
    criterionType: 'VALID_INVALID',
    targetAspect: 'SYNTAX',
    evaluationMethod: {
      engine: 'SCHEMA',
      variableSchema: {
        properties: {
          schemaURL: { type: 'string' }
        }
      },
      implementationTemplate: '{{ schemaURL }}'
    }
  },
  {
    id: uuid(),
    name: 'Property value in range (mock)',
    description: 'Mock template for a GE-based range check',
    criterionType: 'IN_RANGE',
    targetAspect: 'ACCURACY',
    evaluationMethod: {
      engine: 'GREAT_EXPECTATIONS',
      variableSchema: {
        properties: {
          property: { type: "string" },
          minimum: { type: "string" },
          maximum: { type: "string" }
        }
      },
      implementationTemplate: "---\ntype: ExpectColumnValuesToBeBetween\nkwargs:\n  column: {{ property }}\n  min_value: '{{ minimum }}'\n  max_value: '{{ maximum }}'\nmeta:\n  schema:\n    columns:\n      {{ property }}:\n...\n"
    }
  },
  {
    id: uuid(),
    name: 'Property must not be blank',
    description: 'Checks that a selected property contains a non-empty value.',
    criterionType: 'VALID_INVALID',
    targetAspect: 'COMPLETENESS',
    evaluationMethod: {
      engine: 'JQ',
      variableSchema: { properties: { property: { type: 'string' } } },
      implementationTemplate: "if {{ property }} != '' then { success: true, details: '{{ property }} is present' } else { success: false, details: '{{ property }} is blank' } end"
    }
  },
  {
    id: uuid(),
    name: 'Numeric value in range',
    description: 'Checks that a numeric property is between two inclusive limits.',
    criterionType: 'IN_RANGE',
    targetAspect: 'ACCURACY',
    evaluationMethod: {
      engine: 'JQ',
      variableSchema: {
        properties: {
          property: { type: 'string' },
          minimum: { type: 'number' },
          maximum: { type: 'number' }
        }
      },
      implementationTemplate: 'if ({{ property }} >= {{ minimum }}) and ({{ property }} <= {{ maximum }}) then { success: true, details: "{{ property }} is in range" } else { success: false, details: "{{ property }} is outside the allowed range" } end'
    }
  },
  {
    id: uuid(),
    name: 'Required event fields',
    description: 'Checks that an event contains the fields needed for downstream processing.',
    criterionType: 'VALID_INVALID',
    targetAspect: 'SYNTAX',
    evaluationMethod: {
      engine: 'SCHEMA',
      variableSchema: { properties: { schema: { type: 'string' } } },
      implementationTemplate: '{{ schema }}'
    }
  },
  {
    id: uuid(),
    name: 'Column completeness',
    description: 'Checks that a configured tabular column has no empty values.',
    criterionType: 'VALID_INVALID',
    targetAspect: 'COMPLETENESS',
    evaluationMethod: {
      engine: 'GREAT_EXPECTATIONS',
      variableSchema: { properties: { property: { type: 'string' } } },
      implementationTemplate: "---\ntype: ExpectColumnValuesToNotBeNull\nkwargs:\n  column: {{ property }}\nmeta:\n  schema:\n    columns:\n      {{ property }}:\n...\n"
    }
  }
]

let vlaCounter = 1

function findTemplate (id) {
  return templates.find((template) => template.id === id)
}

function validateTemplateModel (body = {}) {
  const evaluationMethod = body.evaluationMethod || {}
  if (!body.name || !body.criterionType || !body.targetAspect || !evaluationMethod.engine || !evaluationMethod.implementationTemplate) {
    return templateFailureFixtures.invalidModel
  }
  return null
}

function responseForTemplate (template, status = 200) {
  return HttpResponse.json(template, { status })
}

export const handlers = [
  http.get('/api/template', () => {
    console.log('Returning mock template list')
    return HttpResponse.json(templates)
  }),

  http.get('/api/template/:id', ({ params }) => {
    const template = findTemplate(params.id)
    return template ? responseForTemplate(template) : responseForFixture(templateFailureFixtures.missingTemplate)
  }),

  http.post('/api/template', async ({ request }) => {
    const body = await request.json()
    const invalid = validateTemplateModel(body)
    if (invalid) return responseForFixture(invalid)

    const template = { ...body, id: uuid() }
    templates.push(template)
    return responseForTemplate(template, 201)
  }),

  http.patch('/api/template/:id', async ({ params, request }) => {
    const index = templates.findIndex((template) => template.id === params.id)
    if (index === -1) return responseForFixture(templateFailureFixtures.missingTemplate)

    const body = await request.json()
    const nextTemplate = { ...templates[index], ...body, id: params.id }
    const invalid = validateTemplateModel(nextTemplate)
    if (invalid) return responseForFixture(invalid)

    templates[index] = nextTemplate
    return responseForTemplate(nextTemplate)
  }),

  http.delete('/api/template/:id', ({ params }) => {
    const index = templates.findIndex((template) => template.id === params.id)
    if (index === -1) return responseForFixture(templateFailureFixtures.missingTemplate)
    const [removed] = templates.splice(index, 1)
    return responseForTemplate(removed)
  }),

  http.post('/api/template/:id/render', async ({ params, request }) => {
    const template = findTemplate(params.id)
    if (!template) return responseForFixture(templateFailureFixtures.missingTemplate)

    const body = await request.json()
    const model = body.model || body
    try {
      const implementation = renderTemplate(template, model)
      return HttpResponse.json(implementation)
    } catch (error) {
      return responseForFixture({
        ...templateFailureFixtures.renderFailure,
        body: { ...templateFailureFixtures.renderFailure.body, details: error.message }
      })
    }
  }),

  http.get('/api/vla', () => {
    console.log('Returning mock VLA list')
    return HttpResponse.json(vlas)
  }),

  http.post('/api/vla/from-templates', async ({ request }) => {
    const body = await request.json()
    console.log('Mock backend received VLA from-templates request:')
    console.log(body)

    const vla = {
      id: uuid(),
      name: body.name || `Mock-generated VLA ${vlaCounter++}`,
      description: body.description,
      participants: body.participants || [],
      dataReference: body.dataReference || '',
      tags: body.tags || [],
      quality: (body.qualityTemplates || []).map(({ id, model }) => {
        const template = findTemplate(id)
        if (template === undefined) {
          throw new Error(`Template ${id} was not found`)
        }

        return renderTemplate(template, model)
      })
    }
    vlas.push(vla)
    console.log('Returning mock response for /api/vla/from-templates request:')
    console.log(vla)

    return HttpResponse.json(vla, { status: 201 })
  }),

  http.post('/api/attestation', async ({ request }) => {
    const body = await request.json()
    console.log('Mock backend received /attestation request:')
    console.log(body)

    if (!body?.credentialSubject || !body?.dataReference) {
      return HttpResponse.json({
        type: 'BAD_REQUEST',
        title: 'Attestation request is incomplete',
        details: 'A credential subject and data reference are required before an attestation can be requested.'
      }, { status: 400 })
    }

    const resp = HttpResponse.json({ id: uuid(), status: 'pending' }, { status: 202 })
    console.log('Returning mock response for /attestation request:')
    console.log(resp)

    return resp
  }),
  
  http.post('/api/evaluate/from-template', async ({ request }) => {
    const body = await request.json()
    console.log('Mock backend received /evaluate/from-template request:')
    console.log(body)

    const { templateID, templateModel = {}, data = {} } = body
    const template = findTemplate(templateID)
    if (template === undefined) {
      return responseForFixture(templateFailureFixtures.missingTemplate)
    }

    if (!templateModel || typeof templateModel !== 'object') {
      return responseForFixture(templateFailureFixtures.invalidModel)
    }

    if (templateModel.forceFailure === 'render') {
      return responseForFixture(templateFailureFixtures.renderFailure)
    }

    const implementation = renderTemplate(template, templateModel)
    const failed = templateModel.forceFailure === true || data?.status === 'invalid' || data?.status === 'failed'
    const details = failed
      ? 'The supplied demo data did not satisfy the selected requirement.'
      : `The ${template.evaluationMethod.engine} check passed for the supplied demo data.`

    const resp = {
      engine: template.evaluationMethod.engine,
      timestamp: new Date().toISOString(),
      success: !failed,
      details,
      implementation: implementation.implementation
    }
    console.log('Returning mock response for /evaluate/from-template request:')
    console.log(resp)

    return HttpResponse.json(resp)
  })
]
