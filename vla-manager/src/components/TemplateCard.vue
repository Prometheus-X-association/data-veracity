<template>
  <n-card size="small" class="template-card" content-style="display:flex;flex-direction:column;height:100%;">
    <div class="template-heading">
      <div class="template-icon">{{ engineShort }}</div>
      <div class="template-title">
        <n-text strong>{{ template.name || 'Unnamed template' }}</n-text>
        <n-text depth="3" class="template-id">{{ template.id }}</n-text>
      </div>
    </div>
    <n-text depth="3" class="template-description">{{ template.description || 'No description provided.' }}</n-text>
    <n-space size="small" :wrap="true" class="template-tags">
      <n-tag size="small" type="info">{{ template.evaluationMethod?.engine || 'Unknown engine' }}</n-tag>
      <n-tag size="small">{{ template.criterionType || 'No criterion' }}</n-tag>
      <n-tag size="small" type="success">{{ template.targetAspect || 'No aspect' }}</n-tag>
    </n-space>
    <div class="template-meta">
      <span>{{ variableCount }} {{ variableCount === 1 ? 'variable' : 'variables' }}</span>
      <span>{{ implementationLabel }}</span>
    </div>
    <template #action>
      <div class="template-actions">
        <n-button size="small" type="primary" ghost @click="$emit('test', template)">Test</n-button>
        <n-button size="small" @click="$emit('edit', template)">Edit</n-button>
        <n-button size="small" type="error" quaternary @click="$emit('remove', template)">Delete</n-button>
      </div>
    </template>
  </n-card>
</template>

<script setup>
import { computed } from 'vue'
import { NButton, NCard, NSpace, NTag, NText } from 'naive-ui'

const props = defineProps({ template: { type: Object, required: true } })
defineEmits(['edit', 'test', 'remove'])

const engineShort = computed(() => ({ SCHEMA: 'SC', JQ: 'JQ', GREAT_EXPECTATIONS: 'GE' }[props.template.evaluationMethod?.engine] || 'RQ'))
const variableCount = computed(() => Object.keys(props.template.evaluationMethod?.variableSchema?.properties || {}).length)
const implementationLabel = computed(() => props.template.evaluationMethod?.implementationTemplate ? 'Implementation ready' : 'Implementation missing')
</script>

<style scoped>
.template-card{height:100%;border-radius:8px}.template-heading{display:flex;align-items:flex-start;gap:10px;min-width:0}.template-icon{display:grid;place-items:center;flex:0 0 36px;width:36px;height:36px;border-radius:8px;color:#0e7490;background:#ecfeff;font-size:.7rem;font-weight:800}.template-title{display:grid;min-width:0;gap:3px}.template-title :deep(.n-text){overflow-wrap:anywhere}.template-id{overflow:hidden;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.62rem;text-overflow:ellipsis;white-space:nowrap}.template-description{display:-webkit-box;min-height:40px;margin-top:14px;overflow:hidden;-webkit-box-orient:vertical;-webkit-line-clamp:2;line-height:1.45}.template-tags{margin-top:14px}.template-meta{display:flex;justify-content:space-between;gap:8px;margin-top:auto;padding-top:16px;color:#64748b;font-size:.68rem}.template-meta span:last-child{text-align:right}.template-actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px}
@media(max-width:520px){.template-actions{justify-content:stretch}.template-actions :deep(.n-button){flex:1 1 80px}.template-meta{align-items:flex-start;flex-direction:column}.template-meta span:last-child{text-align:left}}
</style>
