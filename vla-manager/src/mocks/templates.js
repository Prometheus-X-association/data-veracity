import hb from 'handlebars'

export function renderTemplate(template, model) {
  console.log('Mock-rendering a template')
  const implementationTemplate = template.evaluationMethod?.implementationTemplate
  if (!implementationTemplate) {
    throw new Error(`Template ${template.id} has no implementation template`)
  }
  const implTempl = hb.compile(implementationTemplate)
  return {
    engine: template.evaluationMethod.engine,
    implementation: implTempl(model)
  }
}
