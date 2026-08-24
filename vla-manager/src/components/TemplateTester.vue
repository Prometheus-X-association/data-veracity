<template>
  <n-card class="tester-card" title="Test template" size="small">
    <n-alert v-if="error" type="error" class="tester-error" closable @close="error = null">
      <strong>{{ error.title }}</strong>
      <div>{{ error.message }}</div>
    </n-alert>
    <n-alert v-if="result && result.success === true" type="success" class="tester-result">
      Evaluation passed. The selected data satisfies this requirement.
    </n-alert>
    <FailureExplanation v-if="failure" :failure="failure" heading="Why this test did not pass" />

    <div class="tester-grid">
      <section>
        <div class="section-title"><n-text strong>Template variables</n-text><n-text depth="3">Values used to render the implementation.</n-text></div>
        <TemplateVariableForm :schema="template.evaluationMethod?.variableSchema" v-model:model-value="model" :errors="variableErrors" />
      </section>
      <section>
        <div class="section-title"><n-text strong>Sample data</n-text><n-text depth="3">JSON sent to the evaluation endpoint.</n-text></div>
        <n-input v-model:value="sampleText" type="textarea" :autosize="{ minRows: 12, maxRows: 22 }" placeholder="{ &quot;status&quot;: &quot;valid&quot; }" />
        <n-text depth="3" class="sample-help">Use a status of invalid or failed to exercise a failed demo result.</n-text>
      </section>
    </div>

    <div class="tester-actions">
      <n-button :loading="rendering" @click="runRender">Render implementation</n-button>
      <n-button type="primary" :loading="evaluating" @click="runEvaluation">Evaluate sample data</n-button>
    </div>
    <TemplatePreview :template="template" :value="rendered" class="rendered-preview" />
  </n-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import { NAlert, NButton, NCard, NInput, NText } from 'naive-ui'
import TemplatePreview from './TemplatePreview.vue'
import TemplateVariableForm from './TemplateVariableForm.vue'
import FailureExplanation from './FailureExplanation.vue'
import { evaluateTemplate, renderTemplate } from '../api/templates.js'
import { failureFromCode, normalizeEvaluationResult } from '../failures/failureModel.js'

const props = defineProps({ template: { type: Object, required: true } })
const model = ref({})
const sampleText = ref('{\n  "status": "valid"\n}')
const rendered = ref('')
const result = ref(null)
const failure = ref(null)
const error = ref(null)
const variableErrors = ref({})
const rendering = ref(false)
const evaluating = ref(false)

watch(() => props.template, () => { model.value = {}; rendered.value = ''; result.value = null; failure.value = null; error.value = null }, { immediate: true })

function apiFailure (cause) {
  const code = cause.code === 'NOT_FOUND' ? 'UNKNOWN_TEMPLATE' : cause.code === 'BAD_REQUEST' ? 'INVALID_TEMPLATE_INPUT' : 'GATEWAY_UNAVAILABLE'
  return failureFromCode(code, { evidence: cause.message, retryable: cause.retryable, source: 'template-service' })
}
function parseSample () {
  try { return JSON.parse(sampleText.value) } catch { throw new Error('Sample data is not valid JSON.') }
}
async function runRender () {
  error.value = null
  failure.value = null
  if (!props.template?.id) return
  rendering.value = true
  try {
    const response = await renderTemplate(props.template.id, model.value)
    rendered.value = response.implementation || response.value || ''
  } catch (cause) {
    failure.value = apiFailure(cause)
  } finally { rendering.value = false }
}
async function runEvaluation () {
  error.value = null
  failure.value = null
  result.value = null
  try {
    const data = parseSample()
    evaluating.value = true
    const response = await evaluateTemplate(props.template.id, model.value, data)
    result.value = response
    failure.value = normalizeEvaluationResult(response, { source: 'template-evaluation' })
    if (failure.value.status === 'passed') failure.value = null
    rendered.value = response.implementation || rendered.value
  } catch (cause) {
    failure.value = cause.message === 'Sample data is not valid JSON.'
      ? failureFromCode('INVALID_TEMPLATE_INPUT', { evidence: cause.message, source: 'template-tester' })
      : apiFailure(cause)
  } finally { evaluating.value = false }
}
</script>

<style scoped>
.tester-card{border-radius:8px}.tester-error{margin-bottom:14px}.tester-result{margin-bottom:14px}.tester-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.section-title{display:grid;gap:3px;margin-bottom:10px}.section-title :deep(.n-text:last-child),.sample-help{font-size:.72rem}.sample-help{display:block;margin-top:8px}.tester-actions{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;margin-top:18px}.rendered-preview{margin-top:18px}
@media(max-width:800px){.tester-grid{grid-template-columns:1fr}.tester-actions :deep(.n-button){flex:1;min-height:42px}}
@media(max-width:460px){.tester-actions{display:grid}.tester-actions :deep(.n-button){width:100%}}
</style>
