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

  <div class="page-container builder-container">
    <n-page-header
      title="VLA Builder"
      subtitle="Select JSON nodes from your sample data to attach requirements"
      class="mb-4"
      @back="$router.push('/list')"
    >
      <template #extra>
        <n-space>
          <n-button @click="showSampleModal" type="default">
            <template #icon><n-icon><RefreshIcon /></n-icon></template>
            {{ sampleData ? 'Change Sample Data' : 'Upload Sample Data' }}
          </n-button>
          <n-button
            type="primary"
            size="large"
            @click="handleCreateVLA"
            :disabled="!sampleData || fragments.length === 0"
          >
            Create VLA
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <div v-if="!sampleData" class="empty-state-container">
      <n-empty description="Start by uploading sample data to build your VLA">
        <template #extra>
          <n-button type="primary" size="large" @click="showSampleModal">
            Upload Sample Data
          </n-button>
        </template>
      </n-empty>
    </div>

    <div v-else class="builder-layout">
      <!-- Left Panel: Data Structure -->
      <div class="panel data-panel">
        <n-card title="Data Structure" size="small" class="h-full">
          <n-text depth="3" class="block mb-2">Click on any JSON node to select it for a new requirement.</n-text>
          <div class="json-scroll-area">
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

            <n-tooltip trigger="hover" :disabled="!!lastPath">
              <template #trigger>
                <n-button 
                  type="success" 
                  size="large" 
                  block
                  :disabled="!lastPath"
                  @click="showReqModal"
                >
                  <template #icon><n-icon><LinkIcon /></n-icon></template>
                  Attach Requirement
                </n-button>
              </template>
              You must select a JSON element from the Data Structure first
            </n-tooltip>
          </div>
        </n-card>
      </div>

      <!-- Right Panel: Fragments -->
      <div class="panel fragments-panel">
        <n-card title="Building Blocks (Fragments)" size="small" class="h-full">
          <n-text v-if="fragments.length === 0" depth="3" class="block mb-4 text-center">
            No requirements added yet. Attach them using the toolbox.
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
                  </div>

                  <div v-if="testedFragment === frag && testResult !== null" class="mt-3 p-2 bg-green-50 rounded border border-green-200">
                    <n-text strong type="success" class="text-xs mb-1 block">Test Results:</n-text>
                    <vue-json-pretty :data="testResult" class="text-xs" />
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
  import { ref, toRaw, h, defineComponent } from 'vue'
  import { useRouter } from 'vue-router'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import axios from 'axios'
  import { 
    NPageHeader, NSpace, NButton, NIcon, NEmpty, NCard, 
    NText, NStatistic, NTooltip, NTag, NDivider, NScrollbar, useMessage
  } from 'naive-ui'

  import SampleModal from './SampleModal.vue'
  import ReqModal from './ReqModal.vue'

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

  const message = useMessage()
  const router = useRouter()

  const sampleModal = ref(null)
  const testModal = ref(null)
  const reqModal = ref(null)

  const sampleData = ref(null)
  const testData = ref(null)
  const lastPath = ref(null)
  const fragments = ref([])

  const testedFragment = ref(null)
  const testResult = ref(null)

  const showSampleModal = () => sampleModal.value?.show()
  const showTestModal = (frag) => {
    testModal.value?.show()
    testedFragment.value = frag
    testResult.value = null // reset previous results
  }
  const showReqModal = () => reqModal.value?.show()

  const onNodeClick = (node) => lastPath.value = node.path

  const handleReqAdded = (req) => {
    fragments.value.push(req)
    message.success(`Attached requirement: ${req.requirement.name}`)
  }

  const handleTestDataSelected = async () => {
    const body = {
      templateID: testedFragment.value.data.id,
      templateModel: testedFragment.value.data.model,
      data: testData.value
    }
    try {
      const resp = await axios.post('/api/evaluate/from-template', body)
      testResult.value = resp.data
      message.success('Evaluation complete')
    } catch (err) {
      message.error('Failed to evaluate fragment on the backend.')
      testResult.value = err.response?.data || { error: err.message }
    }
  }

  const handleCreateVLA = async () => {
    const body = {
      description: "Data is recent and valid",
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
      router.push({ path: "/list" })
    } catch (err) {
      message.error('Failed to create VLA on backend.')
    }
  }
</script>

<style scoped>
  .builder-container {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 100px);
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

  .empty-state-container {
    flex-grow: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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

  .toolbox-card {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
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
