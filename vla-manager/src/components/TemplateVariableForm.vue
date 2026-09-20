<template>
  <div class="variable-form">
    <div v-if="!properties.length" class="empty-variables">This template has no variables. Its implementation can be tested as written.</div>
    <n-form-item v-for="field in properties" :key="field.name" :label="field.label" :required="field.required" :validation-status="errors[field.name] ? 'error' : undefined" :feedback="errors[field.name] || field.description">
      <n-input v-if="field.type === 'string'" :value="displayValue(field.name)" :placeholder="field.description || `Value for ${field.name}`" @update:value="value => updateValue(field.name, value)" />
      <n-input-number v-else-if="field.type === 'number' || field.type === 'integer'" :value="numberValue(field.name)" :placeholder="field.description || `Value for ${field.name}`" :precision="field.type === 'integer' ? 0 : undefined" class="full-width" @update:value="value => updateValue(field.name, value)" />
      <n-switch v-else-if="field.type === 'boolean'" :value="Boolean(modelValue[field.name])" @update:value="value => updateValue(field.name, value)" />
      <n-input v-else type="textarea" :value="displayValue(field.name)" :placeholder="field.description || `JSON value for ${field.name}`" :autosize="{ minRows: 2, maxRows: 5 }" @update:value="value => updateValue(field.name, value)" />
    </n-form-item>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NFormItem, NInput, NInputNumber, NSwitch } from 'naive-ui'

const props = defineProps({
  schema: { type: Object, default: () => ({}) },
  modelValue: { type: Object, default: () => ({}) },
  errors: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update:modelValue'])

const properties = computed(() => Object.entries(props.schema?.properties || {}).map(([name, definition = {}]) => ({
  name,
  label: definition.title || name,
  type: definition.type || 'string',
  description: definition.description || '',
  required: props.schema?.required?.includes(name) || definition.required === true
})))

function displayValue (name) {
  const value = props.modelValue[name]
  return value === undefined || value === null ? '' : String(value)
}
function numberValue (name) {
  const value = props.modelValue[name]
  return value === undefined || value === null || value === '' ? null : Number(value)
}
function updateValue (name, value) {
  emit('update:modelValue', { ...props.modelValue, [name]: value })
}
</script>

<style scoped>
.variable-form{display:grid;gap:2px}.empty-variables{padding:12px;border:1px dashed #cbd5e1;border-radius:6px;color:#64748b;background:#f8fafc;font-size:.78rem;line-height:1.5}.full-width{width:100%}
</style>
