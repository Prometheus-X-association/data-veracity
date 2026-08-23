import { HttpResponse } from 'msw'

export const templateFailureFixtures = {
  missingTemplate: {
    status: 404,
    body: {
      type: 'NOT_FOUND',
      title: 'Template was not found',
      details: 'The selected template is not available in this gateway.'
    }
  },
  invalidModel: {
    status: 400,
    body: {
      type: 'BAD_REQUEST',
      title: 'Template input is invalid',
      details: 'One or more required template variables are missing or have the wrong type.'
    }
  },
  renderFailure: {
    status: 400,
    body: {
      type: 'BAD_REQUEST',
      title: 'Requirement could not be rendered',
      details: 'The implementation template could not be rendered with the supplied variables.'
    }
  }
}

export function responseForFixture (fixture) {
  return HttpResponse.json(fixture.body, { status: fixture.status })
}
