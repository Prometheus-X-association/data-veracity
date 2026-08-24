<template>
  <n-card class="editor-card" :title="isEditing ? 'Edit template' : 'Create template'" size="small">
    <template #header-extra><n-button quaternary @click="$emit('cancel')">Close</n-button></template>
    <n-alert v-if="error" type="error" class="editor-error" closable @close="error = null">
      <strong>{{ error.title }}</strong>
      <div>{{ error.message }}</div>
      <small v-if="error.retryable">The gateway may be ready to try again.</small>
    </n-alert>

    <n-form label-placement="top" class="editor-form">
      <div class="editor-grid">
        <n-form-item label="Name" required :validation-status="errors.name ? 'error' : undefined" :feedback="errors.name">
          <n-input v-model:value="form.name" placeholder="For example, Current customer event" />
        </n-form-item>
        <n-form-item label="Quality aspect" required>
          <n-select v-model:value="form.targetAspect" :options="aspectOptions" />
        </n-form-item>
        <n-form-item label="Criterion" required>
          <n-select v-model:value="form.criterionType" :options="criterionOptions" />
        </n-form-item>
        <n-form-item label="Evaluation engine" required>
          <n-select v-model:value="form.evaluationMethod.engine" :options="engineOptions" />
        </n-form-item>
      </div>
      <n-form-item label="Description">
        <n-input v-model:value="form.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="Explain what this requirement checks and when it should be used." />
      </n-form-item>

      <div class="section-heading"><div><n-text strong>Template variables</n-text><n-text depth="3">Add only the values a user must provide when this template is used.</n-text></div><n-button size="small" @click="addVariable">Add variable</n-button></div>
      <div v-if="variableRows.length" class="variable-table">
        <div v-for="row in variableRows" :key="row.name" class="variable-row">
          <n-input :value="row.name" placeholder="Name" @update:value="value => renameVariable(row.name, value)" />
          <n-select :value="row.definition.type || 'string'" :options="variableTypeOptions" @update:value="value => updateVariable(row.name, { type: value })" />
          <n-input :value="row.definition.description" placeholder="Description" @update:value="value => updateVariable(row.name, { description: value })" />
          <n-checkbox :checked="form.evaluationMethod.variableSchema.required?.includes(row.name)" @update:checked="value => toggleRequired(row.name, value)">Required</n-checkbox>
          <n-button quaternary type="error" aria-label="Remove variable" @click="removeVariable(row.name)">Remove</n-button>
        </div>
      </div>
      <n-empty v-else description="No variables yet" size="small" />

      <n-form-item label="Implementation template" required :validation-status="errors.implementation ? 'error' : undefined" :feedback="errors.implementation || 'Use the variable names above in the implementation.'">
        <n-input v-model:value="form.evaluationMethod.implementationTemplate" type="textarea" :autosize="{ minRows: 8, maxRows: 18 }" placeholder="Write the SCHEMA, JQ, or Great Expectations implementation." />
      </n-form-item>
    </n-form>

    <div class="editor-actions">
      <n-button @click="$emit('cancel')">Cancel</n-button>
      <n-button :loading="rendering" :disabled="!canRender" @click="renderCurrent">Preview implementation</n-button>
      <n-button type="primary" :loading="saving" @click="save">{{ isEditing ? 'Save changes' : 'Create template' }}</n-button>
    </div>
    <TemplatePreview :template="form" :value="previewValue" class="preview" />
  </n-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { NAlert, NButton, NCard, NCheckbox, NEmpty, NForm, NFormItem, NInput, NSelect, NText, useMessage } from 'naive-ui'
import TemplatePreview from './TemplatePreview.vue'
import { createTemplate, renderTemplate, updateTemplate } from '../api/templates.js'

const props = defineProps({ template: { type: Object, default: null } })
const emit = defineEmits(['saved', 'cancel'])
const message = useMessage()
const saving = ref(false)
const rendering = ref(false)
const error = ref(null)
const errors = ref({})
const previewValue = ref('')

function blankTemplate () {
  return {
    name: '',
    description: '',
    criterionType: 'VALID_INVALID',
    targetAspect: 'SYNTAX',
    evaluationMethod: { engine: 'SCHEMA', variableSchema: { type: 'object', properties: {}, required: [] }, implementationTemplate: '' }
  }
}
function clone (value) { return JSON.parse(JSON.stringify(value)) }
const form = ref(blankTemplate())
const isEditing = computed(() => Boolean(props.template?.id))
const variableRows = computed(() => Object.entries(form.value.evaluationMethod.variableSchema.properties || {}).map(([name, definition]) => ({ name, definition: definition || {} })))
const canRender = computed(() => Boolean(form.value.id && Object.keys(errors.value).length === 0))

watch(() => props.template, value => { form.value = value ? clone(value) : blankTemplate(); previewValue.value = '' }, { immediate: true })

const engineOptions = [{ label: 'Schema', value: 'SCHEMA' }, { label: 'JQ', value: 'JQ' }, { label: 'Great Expectations', value: 'GREAT_EXPECTATIONS' }]
const criterionOptions = [{ label: 'Valid or invalid', value: 'VALID_INVALID' }, { label: 'In range', value: 'IN_RANGE' }, { label: 'Greater than', value: 'GREATER_THAN' }, { label: 'Less than', value: 'LESS_THAN' }]
const aspectOptions = [{ label: 'Syntax', value: 'SYNTAX' }, { label: 'Timeliness', value: 'TIMELINESS' }, { label: 'Accuracy', value: 'ACCURACY' }, { label: 'Completeness', value: 'COMPLETENESS' }, { label: 'Consistency', value: 'CONSISTENCY' }]
const variableTypeOptions = [{ label: 'Text', value: 'string' }, { label: 'Number', value: 'number' }, { label: 'Integer', value: 'integer' }, { label: 'Boolean', value: 'boolean' }, { label: 'JSON object', value: 'object' }]

function addVariable () {
  const base = 'value'
  let name = base
  let index = 2
  while (form.value.evaluationMethod.variableSchema.properties[name]) name = `${base}${index++}`
  updateVariable(name, { type: 'string', description: '' }, true)
}
function updateVariable (name, patch, create = false) {
  const properties = { ...form.value.evaluationMethod.variableSchema.properties }
  properties[name] = { ...(properties[name] || {}), ...patch }
  form.value.evaluationMethod.variableSchema.properties = properties
  if (create) toggleRequired(name, true)
}
function renameVariable (oldName, nextName) {
  const name = nextName.trim()
  if (!name || name === oldName || form.value.evaluationMethod.variableSchema.properties[name]) return
  const properties = { ...form.value.evaluationMethod.variableSchema.properties }
  properties[name] = properties[oldName]
  delete properties[oldName]
  form.value.evaluationMethod.variableSchema.properties = properties
  form.value.evaluationMethod.variableSchema.required = (form.value.evaluationMethod.variableSchema.required || []).map(item => item === oldName ? name : item)
}
function removeVariable (name) {
  const properties = { ...form.value.evaluationMethod.variableSchema.properties }
  delete properties[name]
  form.value.evaluationMethod.variableSchema.properties = properties
  toggleRequired(name, false)
}
function toggleRequired (name, checked) {
  const current = new Set(form.value.evaluationMethod.variableSchema.required || [])
  checked ? current.add(name) : current.delete(name)
  form.value.evaluationMethod.variableSchema.required = [...current]
}
function validate () {
  const next = {}
  if (!form.value.name.trim()) next.name = 'Enter a name for this template.'
  if (!form.value.evaluationMethod.implementationTemplate.trim()) next.implementation = 'Add the implementation used by the selected engine.'
  errors.value = next
  return Object.keys(next).length === 0
}
function payload () {
  const value = clone(form.value)
  delete value.id
  return value
}
async function save () {
  if (!validate()) return
  saving.value = true
  error.value = null
  try {
    const saved = isEditing.value ? await updateTemplate(form.value.id, payload()) : await createTemplate(payload())
    message.success(isEditing.value ? 'Template updated' : 'Template created')
    emit('saved', saved)
  } catch (cause) {
    error.value = { title: 'Template could not be saved', message: cause.message || 'Check the fields and gateway connection.', retryable: cause.retryable }
  } finally {
    saving.value = false
  }
}
async function renderCurrent () {
  if (!validate() || !form.value.id) return
  rendering.value = true
  error.value = null
  try {
    const result = await renderTemplate(form.value.id, {})
    previewValue.value = result.implementation || result.value || ''
  } catch (cause) {
    error.value = { title: 'Template could not be rendered', message: cause.message || 'Fill in the variables and try again.', retryable: cause.retryable }
  } finally {
    rendering.value = false
  }
}
</script>

<style scoped>
.editor-card{border-radius:8px}.editor-error{margin-bottom:16px}.editor-form{margin-top:4px}.editor-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 16px}.section-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:8px 0 12px}.section-heading>div{display:grid;gap:3px}.section-heading :deep(.n-text:last-child){font-size:.72rem}.variable-table{display:grid;gap:8px;margin-bottom:18px}.variable-row{display:grid;grid-template-columns:1fr 130px 1.5fr auto auto;gap:8px;align-items:center;padding:9px;border:1px solid #e2e8f0;border-radius:6px;background:#f8fafc}.editor-actions{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;margin-top:4px}.preview{margin-top:18px}
@media(max-width:800px){.editor-grid{grid-template-columns:1fr}.variable-row{grid-template-columns:1fr 1fr}.variable-row :deep(.n-input:nth-child(3)){grid-column:1/-1}.variable-row :deep(.n-checkbox){grid-column:1}.variable-row :deep(.n-button){grid-column:2;justify-self:end}}
@media(max-width:480px){.editor-actions{display:grid}.editor-actions :deep(.n-button){width:100%;min-height:42px}.variable-row{grid-template-columns:1fr}.variable-row :deep(.n-input:nth-child(3)),.variable-row :deep(.n-checkbox),.variable-row :deep(.n-button){grid-column:auto}.variable-row :deep(.n-button){justify-self:stretch}}
</style>
