<template>
  <!-- Modals -->
  <SampleModal v-model="sampleData" ref="sampleModal" title="Upload Sample Data for VLA Generation" />
  <SampleModal
    title="Upload Test Data for Fragment"
    v-model="testData"
    ref="testModal"
    @update:modelValue="handleTestDataSelected"
  />
  <ReqModal
    :element="lastPath"
    ref="reqModal"
    @req-added="handleReqAdded"
  />
  <VlaBuilderAssistant
    :key="assistantKey"
    v-model:show="assistantOpen"
    :context="assistantContext"
    :templates="availableTemplates"
    :refresh-templates="refreshTemplates"
    @apply="handleAssistantApply"
    @create-template="handleCreateTemplate"
  />

  <div class="page-container builder-container">
    <n-page-header
      title="VLA Builder"
      subtitle="Select JSON nodes from your sample data to attach requirements"
      class="mb-4"
      @back="$router.push('/list')"
    >
      <template #extra>
        <n-space>
          <n-button secondary @click="assistantOpen = true">
            <template #icon><span aria-hidden="true">✦</span></template>
            Design with AI
          </n-button>
          <n-button secondary @click="router.push('/templates')">
            Template workspace
          </n-button>
          <n-button @click="showSampleModal" type="default">
            <template #icon><n-icon><RefreshIcon /></n-icon></template>
            {{ sampleData ? 'Change Sample Data' : 'Upload Sample Data' }}
          </n-button>
          <n-button
            type="primary"
            size="large"
            @click="handleCreateVLA"
            :disabled="fragments.length === 0 || !metadata.name.trim()"
          >
            Create VLA
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-card title="VLA metadata" size="small" class="metadata-card mb-4">
      <n-text depth="3" class="block metadata-help">
        Name the VLA so it can be identified without relying on its UUID.
      </n-text>
      <n-form-item label="Name" required>
        <n-input v-model:value="metadata.name" placeholder="e.g. Customer events quality" />
      </n-form-item>
      <n-form-item label="Description">
        <n-input v-model:value="metadata.description" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" placeholder="What does this VLA guarantee? (optional)" />
      </n-form-item>
    </n-card>

    <!-- Sample data is optional: the assistant can build a VLA without it,
         and requirements it attaches must stay visible either way. -->
    <div class="builder-layout">
      <!-- Left Panel: Data Structure -->
      <div class="panel data-panel">
        <n-card title="Data Structure" size="small" class="h-full">
          <n-empty v-if="!sampleData" description="No sample data yet (optional)">
            <template #extra>
              <n-text depth="3" class="block mb-2">
                Upload a sample to pick fields for requirements by hand, or let "Design with AI" build the VLA without one.
              </n-text>
              <n-button type="primary" @click="showSampleModal">Upload Sample Data</n-button>
            </template>
          </n-empty>
          <n-text v-else depth="3" class="block mb-2">Click on any JSON node to select it for a new requirement.</n-text>
          <div v-if="sampleData" class="json-scroll-area">
            <vue-json-pretty
              :data="sampleData"
              :showDoubleQuotes="false"
              :showLength="true"
              rootPath=""
              :virtual="true"
              :height="526"
              @node-click="onNodeClick"
            />
          </div>
        </n-card>
      </div>

      <!-- Center Panel: Toolbox -->
      <div class="panel toolbox-panel">
        <n-card title="Toolbox" size="small" class="toolbox-card">
          <div class="toolbox-content">
            <n-statistic label="Selected Element" class="mb-4">
              <template #prefix>
                <n-icon><CodeIcon /></n-icon>
              </template>
              <n-text v-if="!lastPath" depth="3" italic>No element selected</n-text>
              <n-text v-else type="primary" strong class="break-all">{{ lastPath }}</n-text>
            </n-statistic>

            <n-button
              type="success"
              size="large"
              block
              @click="showReqModal"
            >
              <template #icon><n-icon><LinkIcon /></n-icon></template>
              Attach Requirement
            </n-button>
            <n-text depth="3" class="block attach-help">
              Selecting a field in the sample data fills in its path; without a sample, type the path in the requirement.
            </n-text>
          </div>
        </n-card>
      </div>

      <!-- Right Panel: Fragments -->
      <div class="panel fragments-panel">
        <n-card title="Building Blocks (Fragments)" size="small" class="h-full">
          <n-text v-if="fragments.length === 0" depth="3" class="block mb-4 text-center">
            No requirements added yet. Attach them with the toolbox, or let "Design with AI" draft them.
          </n-text>

          <n-scrollbar style="max-height: 550px">
            <div class="fragments-list">
              <div v-for="(frag, index) in fragments" :key="index" class="fragment-block">
                <n-card size="small" :bordered="false" class="block-card">
                  <div class="flex justify-between items-start mb-2">
                    <n-text strong class="text-lg text-primary">{{ frag.requirement.name }}</n-text>
                    <n-tag type="info" size="small">{{ frag.requirement.evaluationMethod.engine }}</n-tag>
                  </div>

                  <div class="bg-gray-50 p-2 rounded mb-2 overflow-x-auto text-xs font-mono">
                    {{ frag.requirement.evaluationMethod.implementationTemplate }}
                  </div>

                  <div class="text-xs mb-2">
                    <vue-json-pretty :data="frag.data" :deep="1" />
                  </div>

                  <n-divider class="my-2" />

                  <div class="flex justify-between items-center">
                    <n-button size="small" ghost type="warning" @click="showTestModal(frag)">
                      Test Fragment
                    </n-button>
                    <n-button size="small" quaternary type="error" @click="removeFragment(index)">
                      Remove
                    </n-button>
                  </div>

                  <div v-if="testedFragment === frag && testOutcome" class="test-outcome" :class="testOutcome.tone" role="status">
                    <strong>{{ testOutcome.title }}</strong>
                    <p v-if="testOutcome.message">{{ testOutcome.message }}</p>
                    <vue-json-pretty v-if="testOutcome.body" :data="testOutcome.body" :deep="2" class="text-xs" />
                  </div>
                </n-card>
              </div>
            </div>
          </n-scrollbar>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, toRaw, h, defineComponent, onActivated, computed, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import axios from 'axios'
  import {
    NPageHeader, NSpace, NButton, NIcon, NEmpty, NCard, NFormItem, NInput,
    NText, NStatistic, NTag, NDivider, NScrollbar, useMessage
  } from 'naive-ui'

  import SampleModal from './SampleModal.vue'
  import ReqModal from './ReqModal.vue'
  import VlaBuilderAssistant from './VlaBuilderAssistant.vue'
  import { evaluateTemplate, listTemplates } from '../api/templates.js'
  import {
    applyVlaAssistantDraft,
    planDraftChanges,
    createBuilderAssistantContext,
    missingTemplateBrief,
    missingTemplateName
  } from '../api/vlaBuilderAssistant.js'

  // Basic SVG Icons
  const RefreshIcon = defineComponent({
    render() {
      return h('svg', { xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 512 512" }, [
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-miterlimit": "10", "stroke-width": "32", d: "M320 146s24.36-12-64-12a160 160 0 10160 160" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M256 58l80 80l-80 80" })
      ])
    }
  })
  const CodeIcon = defineComponent({
    render() {
      return h('svg', { xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 512 512" }, [
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M160 368L32 256l128-112" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M352 368l128-112l-128-112" })
      ])
    }
  })
  const LinkIcon = defineComponent({
    render() {
      return h('svg', { xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 512 512" }, [
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "36", d: "M208 352h-64a96 96 0 010-192h64" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "36", d: "M304 160h64a96 96 0 010 192h-64" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "36", d: "M163.29 256h187.42" })
      ])
    }
  })

  // Named so App.vue's <keep-alive include="CreateView"> keeps the builder's
  // work while the author visits the template workspace.
  defineOptions({ name: 'CreateView' })

  const message = useMessage()
  const router = useRouter()
  const route = useRoute()

  const sampleModal = ref(null)
  const testModal = ref(null)
  const reqModal = ref(null)
  const assistantOpen = ref(false)
  // Bumped to give the assistant a fresh conversation once a VLA is created.
  const assistantKey = ref(0)
  const availableTemplates = ref([])

  const sampleData = ref(null)
  const testData = ref(null)
  const lastPath = ref(null)
  const fragments = ref([])
  const metadata = ref({ name: '', description: '' })
  const testedFragment = ref(null)
  const testOutcome = ref(null)

  const showSampleModal = () => sampleModal.value?.show()
  const showTestModal = (frag) => {
    testModal.value?.show()
    testedFragment.value = frag
    testOutcome.value = null // reset previous results
  }
  const showReqModal = () => reqModal.value?.show()

  const onNodeClick = (node) => lastPath.value = node.path

  const assistantContext = computed(() => createBuilderAssistantContext({
    metadata: metadata.value,
    sampleData: sampleData.value,
    selectedPath: lastPath.value,
    fragments: fragments.value
  }))

  const removeFragment = (index) => {
    const [removed] = fragments.value.splice(index, 1)
    if (testedFragment.value === removed) testOutcome.value = null
    message.info(`Removed requirement: ${removed?.requirement?.name || "requirement"}`)
  }

  const handleReqAdded = (req) => {
    fragments.value.push(req)
    message.success(`Attached requirement: ${req.requirement.name}`)
  }

  // The drawer hands over only the requirements that passed validation, and
  // the metadata only when the author opted in.
  const handleAssistantApply = (selection) => {
    try {
      // The draft is the VLA's complete requirement list, so the builder is
      // made to match it: requirements are added and removed.
      const { add, remove } = planDraftChanges(fragments.value, selection.requirements)
      const next = applyVlaAssistantDraft(
        { metadata: metadata.value, fragments: fragments.value },
        selection,
        availableTemplates.value,
        { includeMetadata: selection.includeMetadata, replaceRequirements: true }
      )
      metadata.value = next.metadata
      fragments.value = next.fragments
      assistantOpen.value = false
      const count = n => `${n} requirement${n === 1 ? '' : 's'}`
      const parts = []
      if (add.length) parts.push(`added ${count(add.length)}`)
      if (remove.length) parts.push(`removed ${count(remove.length)}`)
      if (selection.includeMetadata) parts.push('filled in the metadata')
      const summary = parts.join(', ') || 'nothing changed'
      message.success(`Assistant draft applied: ${summary}.`)
    } catch (cause) {
      message.error(cause.message || 'The assistant draft could not be applied.')
    }
  }

  // One sub-session per missing template: the builder (and the assistant's
  // conversation) is kept alive meanwhile, and this template's rule alone
  // seeds the template assistant.
  const handleCreateTemplate = (item) => {
    const brief = missingTemplateBrief(item)
    assistantOpen.value = false
    router.push({ path: '/templates', query: { mode: 'create', from: 'builder', ...(brief ? { brief } : {}) } })
    message.info(`Creating “${missingTemplateName(item)}”. Your builder work and conversation are kept.`)
  }

  // A test has three outcomes that must not look alike: the data passed,
  // the data failed the requirement, or the requirement could not be run.
  const handleTestDataSelected = async () => {
    const { id, model } = testedFragment.value.data
    try {
      const result = await evaluateTemplate(id, model, testData.value)
      testOutcome.value = result.success
        ? { tone: 'passed', title: 'The test data satisfies this requirement', message: result.details, body: result }
        : { tone: 'failed', title: 'The test data does not satisfy this requirement', message: result.details, body: result }
    } catch (cause) {
      // An evaluation the engine could not run still carries its result.
      const body = cause.details && Object.keys(cause.details).length ? cause.details : null
      testOutcome.value = {
        tone: 'error',
        title: 'The requirement could not be evaluated',
        message: body?.error || cause.message,
        body
      }
      message.error(testOutcome.value.message || 'The fragment could not be evaluated.')
    }
  }

  const handleCreateVLA = async () => {
    const description = metadata.value.description.trim()
    const body = {
      name: metadata.value.name.trim(),
      // Optional, so left out rather than sent empty.
      ...(description ? { description } : {}),
      schema: {
        properties: {
          timestamp: { type: "string" },
          result: { type: "integer" }
        }
      },
      qualityTemplates: [...toRaw(fragments.value.map((f) => f.data))]
    }

    try {
      await axios.post('/api/vla/from-templates', body)
      message.success(`Successfully created VLA from ${fragments.value.length} fragments`)
      // The view is kept alive, so the next visit would otherwise reopen
      // the VLA that was just saved.
      resetBuilder()
      router.push({ path: "/list" })
    } catch (err) {
      message.error(err.response?.data?.details || err.response?.data?.title || 'The VLA could not be created.')
    }
  }

  const resetBuilder = () => {
    sampleData.value = null
    testData.value = null
    lastPath.value = null
    fragments.value = []
    metadata.value = { name: '', description: '' }
    testedFragment.value = null
    testOutcome.value = null
    assistantOpen.value = false
    assistantKey.value++
  }

  // A failed refresh keeps the catalog already loaded rather than emptying it.
  const refreshTemplates = async () => {
    try {
      const templates = await listTemplates()
      availableTemplates.value = Array.isArray(templates) ? templates : []
    } catch {
      // The assistant still works against the last catalog it saw.
    }
  }

  // Runs on the first visit and on every return: templates created in the
  // meantime show up in the catalog.
  onActivated(() => {
    // Returning from a template sub-session reopens the assistant on the
    // conversation it was started from.
    if (route.query.assistant === 'open') {
      assistantOpen.value = true
      router.replace({ path: '/create' })
    }
    return refreshTemplates()
  })
  watch(assistantOpen, open => { if (open) refreshTemplates() })
</script>

<style scoped>
  .attach-help { margin-top: 8px; font-size: .75rem; }

  .test-outcome {
    display: grid;
    gap: 4px;
    margin-top: 12px;
    padding: 8px 10px;
    border: 1px solid;
    border-radius: 6px;
    font-size: .75rem;
  }
  .test-outcome p { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
  .test-outcome.passed { border-color: #a7f3d0; background: #f0fdf4; color: #065f46; }
  .test-outcome.failed { border-color: #fcd34d; background: #fffbeb; color: #78350f; }
  .test-outcome.error { border-color: #fecaca; background: #fef2f2; color: #991b1b; }

  .builder-container {
    display: flex;
    flex-direction: column;
    min-height: calc(100vh - 100px);
  }

  .mb-4 { margin-bottom: 16px; }
  .mb-2 { margin-bottom: 8px; }
  .mt-3 { margin-top: 12px; }
  .my-2 { margin-top: 8px; margin-bottom: 8px; }
  .block { display: block; }
  .h-full { height: 100%; }
  .text-center { text-align: center; }
  .text-lg { font-size: 1.125rem; }
  .text-xs { font-size: 0.75rem; }
  .font-mono { font-family: monospace; }
  .break-all { word-break: break-all; }
  .flex { display: flex; }
  .justify-between { justify-content: space-between; }
  .items-start { align-items: flex-start; }
  .items-center { align-items: center; }
  .p-2 { padding: 8px; }
  .bg-gray-50 { background-color: #f9fafb; }
  .bg-green-50 { background-color: #f0fdf4; }
  .border { border-width: 1px; border-style: solid; }
  .border-green-200 { border-color: #bbf7d0; }
  .rounded { border-radius: 4px; }
  .overflow-x-auto { overflow-x: auto; }
  .text-primary { color: #2563eb; }

  .metadata-card {
    flex: none;
  }

  .metadata-help {
    margin-bottom: 12px;
  }







  .builder-layout {
    display: grid;
    grid-template-columns: 2fr 1fr 2fr;
    gap: 16px;
    flex-grow: 1;
    min-height: 0;
    width: 100%;
  }

  .panel {
    display: flex;
    flex-direction: column;
    min-height: 0;
    min-width: 0;
  }

  .toolbox-panel {
    align-self: center;
  }

  .builder-container :deep(.n-page-header) {
    gap: 16px;
  }

  .builder-container :deep(.n-page-header__main) {
    min-width: 0;
  }

  .builder-container :deep(.n-page-header__extra) {
    min-width: 0;
  }

  .builder-container :deep(.n-button) {
    min-height: 40px;
  }

  .toolbox-card {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
  }

  @media (max-width: 900px) {
    .builder-container {
      height: auto;
    }


    .builder-layout {
      grid-template-columns: 1fr;
      flex-grow: 0;
    }

    .toolbox-panel {
      align-self: stretch;
    }

    .json-scroll-area {
      height: min(550px, 50vh);
    }
  }

  @media (max-width: 700px) {
    .builder-container :deep(.n-page-header) {
      align-items: flex-start;
    }

    .builder-container :deep(.n-page-header__extra),
    .builder-container :deep(.n-page-header__extra .n-space) {
      width: 100%;
    }

    .builder-container :deep(.n-page-header__extra .n-space) {
      flex-wrap: wrap;
      justify-content: flex-start;
    }

    .builder-container :deep(.n-page-header__extra .n-button) {
      flex: 1 1 180px;
    }


    .json-scroll-area {
      height: min(480px, 55vh);
      padding: 8px;
    }

    .fragment-block:hover {
      border-color: #e2e8f0;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    .builder-layout .panel :deep(.n-card__content) {
      min-height: 0;
    }
  }

  .toolbox-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .json-scroll-area {
    background: #f8fafc;
    border-radius: 6px;
    padding: 12px;
    border: 1px solid #e2e8f0;
    overflow-x: auto;
    overflow-y: hidden;
    height: 550px;
    box-sizing: border-box;
  }

  /* Prevent vue-json-pretty from aggressively breaking words in narrow containers */
  ::v-deep(.vjs-tree) {
    word-break: normal !important;
    white-space: nowrap !important;
  }
  ::v-deep(.vjs-value) {
    word-break: normal !important;
  }

  .fragments-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding-right: 8px;
  }

  .fragment-block {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
  }

  .fragment-block:hover {
    border-color: #0891b2;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }

  .block-card {
    background: transparent;
  }

  ::v-deep(.n-card__content) {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
</style>
