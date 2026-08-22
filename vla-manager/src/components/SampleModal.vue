<template>
  <n-modal
    v-model:show="showModalFlag"
    preset="card"
    :title="props.title ?? 'Insert Sample JSON'"
    class="sample-modal"
    size="huge"
    :style="{ width: 'min(1100px, calc(100vw - 24px))', maxWidth: 'calc(100vw - 24px)', maxHeight: 'calc(100vh - 24px)' }"
  >
    <div class="modal-body">
      <!-- File Upload -->
      <n-upload
        :custom-request="handleUploadRequest"
        :show-file-list="false"
        accept=".json"
      >
        <n-upload-dragger>
          <div style="margin-bottom: 12px">
            <n-icon size="48" :depth="3">
              <UploadIcon />
            </n-icon>
          </div>
          <n-text style="font-size: 16px">
            Click or drag a JSON file to this area to upload
          </n-text>
        </n-upload-dragger>
      </n-upload>

      <n-divider>OR</n-divider>

      <!-- Dev Picker -->
      <div>
        <n-text strong class="block mb-2">Choose a sample:</n-text>
        <n-space>
          <n-button
            v-for="d in dummySamples"
            :key="d.name"
            secondary
            type="info"
            @click="loadSample(d.name)"
          >
            {{ d.name }}
          </n-button>
        </n-space>
      </div>

      <n-divider>OR</n-divider>

      <!-- Text Input -->
      <div class="paste-area">
        <n-text strong class="block mb-2">Paste JSON here:</n-text>
        <div class="split-view">
          <n-input
            v-model:value="jsonText"
            type="textarea"
            placeholder="Paste your JSON here..."
            :autosize="{ minRows: 10, maxRows: 15 }"
            @input="handleTextInput"
            class="json-textarea"
          />
          <div class="json-preview">
            <vue-json-pretty
              v-if="parsedData"
              :data="parsedData"
              :virtual="true"
              :height="474"
              :showLineNumber="true"
              :showDoubleQuotes="false"
            />
            <div v-else class="empty-preview">
              <n-text depth="3">Preview will appear here</n-text>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <n-alert v-if="error" type="error" class="mt-4">
        {{ error }}
      </n-alert>
    </div>
    
    <template #footer>
      <n-space justify="end">
        <n-button @click="clearAll">
          Clear
        </n-button>
        <n-button type="primary" @click="selectSample" :disabled="!parsedData">
          Select JSON
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup>
  import { ref, watch, h, defineComponent } from 'vue'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import { 
    NModal, NUpload, NUploadDragger, NIcon, NText, NDivider, 
    NSpace, NButton, NInput, NAlert 
  } from 'naive-ui'
  import movieJson from '../data/movie.json'
  import xapiJson from '../data/xapi.json'

  const UploadIcon = defineComponent({
    render() {
      return h('svg', { xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 512 512" }, [
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M320 367.79h76c55 0 100-29.21 100-83.6s-53-81.47-96-83.6c-8.89-85.06-71-136.8-144-136.8c-69 0-113.44 45.79-128 91.2c-60 5.7-112 43.88-112 106.4s54 106.4 120 106.4h56" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M320 255.79l-64-64l-64 64" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M256 448.21V207.79" })
      ])
    }
  })

  const dummySamples = [
    { name: 'Movie', sample: movieJson },
    { name: 'xAPI Statement', sample: xapiJson },
  ]

  const showModalFlag = ref(false)
  const jsonText = ref('')
  const error = ref(null)
  const parsedData = ref(null)

  const showModal = () => {
    showModalFlag.value = true
  }

  const loadSample = (name) => {
    const sample = dummySamples.find((s) => s.name === name)
    jsonText.value = JSON.stringify(sample.sample, null, 2)
    parseJSON()
  }

  const handleUploadRequest = ({ file, onFinish, onError }) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        jsonText.value = e.target.result
        parseJSON()
        onFinish()
      } catch (err) {
        error.value = `Failed to read file: ${err.message}`
        onError()
      }
    }
    reader.onerror = () => {
      error.value = 'Failed to read file'
      onError()
    }
    reader.readAsText(file.file)
  }

  const handleTextInput = () => {
    if (error.value) error.value = null
    parseJSON()
  }

  const parseJSON = () => {
    if (!jsonText.value.trim()) {
      parsedData.value = null
      error.value = null
      return
    }
    try {
      parsedData.value = JSON.parse(jsonText.value)
      error.value = null
    } catch (err) {
      error.value = `Invalid JSON: ${err.message}`
      parsedData.value = null
    }
  }

  const clearAll = () => {
    jsonText.value = ''
    parsedData.value = null
    error.value = null
  }

  const props = defineProps({ modelValue: Object, title: String })
  defineExpose({ show: showModal })

  const emit = defineEmits(['update:modelValue'])

  const selectSample = () => {
    emit('update:modelValue', parsedData.value)
    showModalFlag.value = false
  }

  // Watch for external clearing
  watch(() => props.modelValue, (newVal) => {
    if (!newVal) {
      clearAll()
    }
  })
</script>

<style scoped>
  .modal-body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: calc(90vh - 160px);
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 8px;
  }
  
  .split-view {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    align-items: stretch;
  }

  .json-textarea {
    height: 500px;
  }
  
  /* Fix textarea internal element for Naive UI */
  ::v-deep(.n-input__textarea-el) {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    letter-spacing: normal !important;
    padding: 12px !important;
    white-space: pre !important;
    overflow-wrap: normal !important;
    overflow-x: auto !important;
  }
  
  .json-preview {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 12px;
    overflow-x: auto;
    overflow-y: hidden;
    height: 500px;
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

  .empty-preview {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mb-2 {
    margin-bottom: 8px;
  }
  .mt-4 {
    margin-top: 16px;
  }
  .block {
    display: block;
  }

  :deep(.n-card) {
    max-width: 100%;
  }

  :deep(.n-card__content),
  :deep(.n-card__footer) {
    min-width: 0;
  }

  :deep(.n-card__footer .n-space) {
    flex-wrap: wrap;
  }

  @media (max-width: 700px) {
    .modal-body {
      gap: 12px;
      max-height: calc(100vh - 150px);
      padding-right: 0;
    }

    .split-view {
      grid-template-columns: 1fr;
      gap: 12px;
    }

    .json-textarea,
    .json-preview {
      height: min(360px, 42vh);
    }

    .json-preview {
      padding: 8px;
    }

    :deep(.n-card__footer .n-space) {
      width: 100%;
      justify-content: stretch;
    }

    :deep(.n-card__footer .n-button) {
      flex: 1 1 120px;
      min-height: 44px;
    }
  }
</style>
