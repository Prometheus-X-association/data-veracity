<template>
  <div class="page-container templates-page">
    <n-page-header title="VLA templates" subtitle="Create reusable quality requirements for new agreements">
      <template #extra>
        <n-space>
          <n-button @click="loadTemplates">Refresh</n-button>
          <n-button type="primary" @click="openCreate">Create template</n-button>
        </n-space>
      </template>
    </n-page-header>

    <div class="summary-grid">
      <n-card size="small"><n-statistic label="Available templates" :value="templates.length" /></n-card>
      <n-card size="small"><n-statistic label="Engines in use" :value="engineCount" /></n-card>
      <n-card size="small"><n-statistic label="Visible results" :value="filteredTemplates.length" /></n-card>
    </div>

    <n-alert v-if="error" type="error" closable @close="error = null">
      <strong>{{ error.title }}</strong>
      <div>{{ error.message }}</div>
      <n-button text type="primary" @click="loadTemplates">Try again</n-button>
    </n-alert>

    <n-alert v-if="activeMode && activeMode !== 'create' && !activeTemplate" type="warning">
      This template is no longer available. Refresh the list and choose another template.
    </n-alert>
    <TemplateEditor v-if="activeMode === 'create' || (activeMode === 'edit' && activeTemplate)" :template="activeMode === 'edit' ? activeTemplate : null" @saved="handleSaved" @cancel="closeWorkspace" />
    <TemplateTester v-if="activeMode === 'test' && activeTemplate" :template="activeTemplate" />

    <TemplateFilters v-model:query="query" v-model:engine="engine" v-model:aspect="aspect" @clear="clearFilters" />

    <n-spin :show="loading">
      <div v-if="filteredTemplates.length" class="template-grid">
        <TemplateCard v-for="template in filteredTemplates" :key="template.id" :template="template" @edit="openEdit" @test="openTest" @remove="removeTemplate" />
      </div>
      <n-empty v-else description="No templates match these filters.">
        <template #extra><n-button type="primary" @click="openCreate">Create the first template</n-button></template>
      </n-empty>
    </n-spin>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDialog, useMessage, NAlert, NButton, NCard, NEmpty, NPageHeader, NSpace, NSpin, NStatistic } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import TemplateCard from './TemplateCard.vue'
import TemplateFilters from './TemplateFilters.vue'
import TemplateEditor from './TemplateEditor.vue'
import TemplateTester from './TemplateTester.vue'
import { deleteTemplate, listTemplates } from '../api/templates.js'

const router = useRouter()
const route = useRoute()
const dialog = useDialog()
const message = useMessage()
const templates = ref([])
const loading = ref(false)
const error = ref(null)
const query = ref('')
const engine = ref(null)
const aspect = ref(null)
const activeMode = computed(() => String(route.query.mode || ''))
const activeTemplate = computed(() => templates.value.find(template => String(template.id) === String(route.query.id)))

const filteredTemplates = computed(() => templates.value.filter(template => {
  const text = `${template.name || ''} ${template.description || ''} ${template.id || ''}`.toLowerCase()
  return text.includes(query.value.toLowerCase()) && (!engine.value || template.evaluationMethod?.engine === engine.value) && (!aspect.value || template.targetAspect === aspect.value)
}))
const engineCount = computed(() => new Set(templates.value.map(template => template.evaluationMethod?.engine).filter(Boolean)).size)

async function loadTemplates () {
  loading.value = true
  error.value = null
  try {
    const data = await listTemplates()
    templates.value = Array.isArray(data) ? data : []
  } catch (cause) {
    error.value = { title: 'Templates could not be loaded', message: cause.message || 'Check the gateway connection and try again.' }
  } finally {
    loading.value = false
  }
}

function openCreate () { router.push({ path: '/templates', query: { mode: 'create' } }) }
function openEdit (template) { router.push({ path: '/templates', query: { mode: 'edit', id: template.id } }) }
function openTest (template) { router.push({ path: '/templates', query: { mode: 'test', id: template.id } }) }
async function handleSaved (template) {
  await loadTemplates()
  router.replace({ path: '/templates' })
  message.success(`Saved ${template.name || 'template'}`)
}
function closeWorkspace () { router.replace({ path: '/templates' }) }
function clearFilters () { query.value = ''; engine.value = null; aspect.value = null }

function removeTemplate (template) {
  dialog.warning({
    title: 'Delete template',
    content: `Delete “${template.name}”? Existing VLAs are not changed.`,
    positiveText: 'Delete',
    negativeText: 'Keep it',
    onPositiveClick: async () => {
      try {
        await deleteTemplate(template.id)
        templates.value = templates.value.filter(item => item.id !== template.id)
        message.success('Template deleted')
      } catch (cause) {
        message.error(cause.message || 'The template could not be deleted.')
      }
    }
  })
}

onMounted(loadTemplates)
</script>

<style scoped>
.templates-page{display:grid;gap:18px}.summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.template-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.templates-page :deep(.n-page-header){gap:16px}.templates-page :deep(.n-page-header__main){min-width:0}.templates-page :deep(.n-page-header__title){overflow-wrap:anywhere}.templates-page :deep(.n-alert){line-height:1.5}.templates-page :deep(.n-alert__content){min-width:0}.templates-page :deep(.n-spin-container){min-height:160px}
@media(max-width:1050px){.template-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){.summary-grid{grid-template-columns:1fr}.template-grid{grid-template-columns:1fr}.templates-page :deep(.n-page-header){align-items:flex-start}.templates-page :deep(.n-page-header__extra),.templates-page :deep(.n-page-header__extra .n-space){width:100%}.templates-page :deep(.n-page-header__extra .n-button){flex:1;min-height:42px}}
</style>
