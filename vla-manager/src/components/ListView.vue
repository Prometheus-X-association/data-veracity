<template>
  <SampleModal v-model="data" ref="sampleModal" @update:modelValue="onDataSelected" title="Try VLA with Sample Data" />
  <div class="page-container">
    <n-page-header
      title="View VLAs"
      subtitle="Manage and test your Veracity Level Agreements"
      class="mb-6"
    >
      <template #extra>
        <n-space>
          <n-button secondary @click="$router.push('/templates')">Template workspace</n-button>
          <n-button type="primary" size="large" @click="$router.push('/create')">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            Create New VLA
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-modal
      v-model:show="trialOpen"
      preset="card"
      :title="trial ? `Sample run: ${trial.name}` : 'Sample run'"
      :style="{ width: 'min(820px, calc(100vw - 24px))' }"
    >
      <n-spin :show="!!trial?.loading">
        <div v-if="trial" class="trial-body">
          <n-alert v-if="trial.error" type="error">{{ trial.error }}</n-alert>
          <template v-else-if="!trial.loading">
            <n-alert :type="trialTone" :show-icon="true">
              {{ trialSummary }}
              <n-text depth="3" class="block trial-note">A dry run over the sample: nothing was attested.</n-text>
            </n-alert>
            <div v-for="(row, index) in trial.rows" :key="index" class="trial-row" :class="row.tone">
              <div class="trial-row-head">
                <EngineBadge :engine="row.requirement.engine" />
                <strong>{{ TONE_LABELS[row.tone] }}</strong>
              </div>
              <p v-if="row.result.error || row.result.details" class="trial-message">
                {{ row.result.error || row.result.details }}
              </p>
              <pre class="trial-implementation">{{ row.requirement.implementation }}</pre>
            </div>
          </template>
        </div>
      </n-spin>
    </n-modal>

    <n-spin :show="loading">
      <div v-if="vlas.length > 0">
        <n-grid x-gap="16" y-gap="16" cols="1 s:2 m:3 l:4" responsive="screen">
          <n-grid-item v-for="vla in vlas" :key="vla.id">
            <n-card :title="vla.name || vlaPurpose(vla) || 'Unnamed VLA'" hoverable class="vla-card">
              <template #header-extra>
                <n-tag type="info" size="small" round>VLA</n-tag>
              </template>

              <div class="vla-content">
                <n-text depth="3" class="vla-desc">{{ vlaPurpose(vla) || 'No description provided' }}</n-text>

                <div class="metadata-list">
                  <div v-if="vla.dataReference" class="metadata-row">
                    <n-text strong>Data</n-text>
                    <n-text depth="2">{{ vla.dataReference }}</n-text>
                  </div>
                  <div v-if="vla.participants?.length" class="metadata-row">
                    <n-text strong>Participants</n-text>
                    <n-space size="small" :wrap="true">
                      <n-tag v-for="participant in vla.participants" :key="participant" size="small" type="warning">
                        {{ participant }}
                      </n-tag>
                    </n-space>
                  </div>
                  <div v-if="vla.tags?.length" class="metadata-row">
                    <n-text strong>Tags</n-text>
                    <n-space size="small" :wrap="true">
                      <n-tag v-for="tag in vla.tags" :key="tag" size="small" round>{{ tag }}</n-tag>
                    </n-space>
                  </div>
                </div>

                <n-divider class="my-3" />

                <div class="engine-tags">
                  <n-text strong class="block mb-2">Engines:</n-text>
                  <n-space size="small">
                    <n-tag
                      v-for="engine in new Set(vlaRequirements(vla).map(q => q.engine))"
                      :key="engine"
                      type="success"
                      size="small"
                      bordered
                    >
                      {{ engine }}
                    </n-tag>
                  </n-space>
                </div>
              </div>

              <template #action>
                <n-space justify="end">
                  <n-tooltip trigger="hover">
                    <template #trigger>
                      <n-button
                        type="primary"
                        ghost
                        @click.stop="showModalAndSetFields(vla)"
                      >
                        Try with Sample
                      </n-button>
                    </template>
                    Test this VLA using sample data
                  </n-tooltip>
                </n-space>
                <n-text depth="3" class="vla-id">ID: {{ vla.id }}</n-text>
              </template>
            </n-card>
          </n-grid-item>
        </n-grid>
      </div>

      <n-empty v-else-if="!loading" description="No VLAs found. Create one to get started!">
        <template #extra>
          <n-button type="primary" @click="$router.push('/create')">
            Create First VLA
          </n-button>
        </template>
      </n-empty>
    </n-spin>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, h, defineComponent } from 'vue'
  import axios from 'axios'
  import {
    NCard, NButton, NPageHeader, NGrid, NGridItem, NModal,
    NTag, NSpace, NText, NDivider, NTooltip, NEmpty, NIcon, NSpin, NAlert, useMessage
  } from 'naive-ui'
  import SampleModal from './SampleModal.vue'
  import EngineBadge from './EngineBadge.vue'
  import { evaluateVla } from '../api/templates.js'
  import { vlaPurpose, vlaRequirements } from '../api/vla.js'

  // We define a simple SVG icon for Add to avoid external icon dependencies
  const AddIcon = defineComponent({
    render() {
      return h('svg', { xmlns: "http://www.w3.org/2000/svg", viewBox: "0 0 512 512" }, [
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M256 112v288" }),
        h('path', { fill: "none", stroke: "currentColor", "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "32", d: "M400 256H112" })
      ])
    }
  })

  const message = useMessage()
  const vlas = ref([])
  const loading = ref(true)

  const sampleModal = ref(null)

  const selectedVLA = ref(null)

  const showModalAndSetFields = (vla) => {
    selectedVLA.value = vla
    sampleModal.value?.show()
  }

  const data = ref(null)
  const trial = ref(null)
  const trialOpen = ref(false)

  // A dry run: each requirement is evaluated over the sample, as "Test
  // Fragment" does in the builder, and nothing is attested.
  const onDataSelected = async (newData) => {
    const vla = selectedVLA.value
    if (!vla) return
    const quality = vlaRequirements(vla)
    trial.value = { name: vla.name || vlaPurpose(vla) || 'VLA', loading: true, rows: [], error: null }
    trialOpen.value = true
    try {
      const results = await evaluateVla(vla.id, newData)
      trial.value.rows = quality.map((requirement, index) => {
        const result = results[index] || {}
        const tone = result.error ? 'error' : result.success ? 'passed' : 'failed'
        return { requirement, result, tone }
      })
    } catch (cause) {
      trial.value.error = cause.message || 'The VLA could not be evaluated.'
      message.error(trial.value.error)
    } finally {
      trial.value.loading = false
      selectedVLA.value = null
    }
  }

  const trialSummary = computed(() => {
    const rows = trial.value?.rows || []
    const passed = rows.filter(row => row.tone === 'passed').length
    if (!rows.length) return 'This VLA has no requirements to evaluate.'
    return `${passed} of ${rows.length} requirement${rows.length === 1 ? '' : 's'} passed.`
  })
  const trialTone = computed(() => {
    const rows = trial.value?.rows || []
    if (rows.some(row => row.tone === 'error')) return 'error'
    if (rows.some(row => row.tone === 'failed')) return 'warning'
    return 'success'
  })
  const TONE_LABELS = { passed: 'Passed', failed: 'Not satisfied', error: 'Could not run' }

  onMounted(async () => {
    try {
      const response = await axios.get('/api/vla')
      vlas.value = response.data
    } catch (error) {
      message.error('Failed to load VLAs from server.')
    } finally {
      loading.value = false
    }
  })
</script>

<style scoped>
  .mb-6 {
    margin-bottom: 24px;
  }

  .trial-body {
    display: grid;
    gap: 12px;
    min-height: 60px;
  }
  .trial-note { font-size: .75rem; margin-top: 2px; }
  .trial-row {
    display: grid;
    gap: 6px;
    padding: 10px 12px;
    border: 1px solid;
    border-radius: 6px;
    font-size: .8rem;
  }
  .trial-row.passed { border-color: #a7f3d0; background: #f0fdf4; color: #065f46; }
  .trial-row.failed { border-color: #fcd34d; background: #fffbeb; color: #78350f; }
  .trial-row.error { border-color: #fecaca; background: #fef2f2; color: #991b1b; }
  .trial-row-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
  .trial-message { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }
  .trial-implementation {
    margin: 0;
    max-height: 160px;
    overflow: auto;
    padding: 8px;
    border-radius: 4px;
    color: #334155;
    background: rgba(255, 255, 255, .7);
    font: .72rem/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
  .mb-2 {
    margin-bottom: 8px;
  }
  .my-3 {
    margin-top: 12px;
    margin-bottom: 12px;
  }
  .block {
    display: block;
  }

  .vla-card {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .vla-content {
    flex-grow: 1;
  }

  .vla-desc {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .metadata-list {
    display: grid;
    gap: 8px;
    margin-top: 14px;
  }

  .metadata-row {
    display: grid;
    gap: 4px;
  }

  .vla-id {
    display: block;
    margin-top: 10px;
    font-family: monospace;
    font-size: 0.7rem;
    word-break: break-all;
  }

  :deep(.n-page-header) {
    gap: 16px;
  }

  :deep(.n-page-header__main) {
    min-width: 0;
  }

  :deep(.n-page-header__title) {
    overflow-wrap: anywhere;
  }

  :deep(.n-card__header) {
    min-width: 0;
  }

  :deep(.n-card__header-main) {
    min-width: 0;
    overflow-wrap: anywhere;
  }

  :deep(.n-button) {
    min-height: 40px;
  }

  @media (max-width: 700px) {
    .mb-6 { margin-bottom: 18px; }
    :deep(.n-page-header) { align-items: flex-start; }
    :deep(.n-page-header__extra) { width: 100%; }
    :deep(.n-page-header__extra .n-button) { width: 100%; }
    .metadata-row :deep(.n-text) { overflow-wrap: anywhere; }
    .vla-id { overflow-wrap: anywhere; }
  }
</style>
