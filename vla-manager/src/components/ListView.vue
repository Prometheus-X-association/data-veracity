<template>
  <SampleModal v-model="data" ref="sampleModal" @update:modelValue="onDataSelected" title="Try VLA with Sample Data" />
  <div class="page-container">
    <n-page-header
      title="View VLAs"
      subtitle="Manage and test your Veracity Level Agreements"
      class="mb-6"
    >
      <template #extra>
        <n-button type="primary" size="large" @click="$router.push('/create')">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
          Create New VLA
        </n-button>
      </template>
    </n-page-header>

    <n-spin :show="loading">
      <div v-if="vlas.length > 0">
        <n-grid x-gap="16" y-gap="16" cols="1 s:2 m:3 l:4" responsive="screen">
          <n-grid-item v-for="vla in vlas" :key="vla.id">
            <n-card :title="vla.id" hoverable class="vla-card">
              <template #header-extra>
                <n-tag type="info" size="small" round>VLA</n-tag>
              </template>
              
              <div class="vla-content">
                <n-text depth="3" class="vla-desc">{{ vla.description || 'No description provided' }}</n-text>
                
                <n-divider class="my-3" />
                
                <div class="engine-tags">
                  <n-text strong class="block mb-2">Engines:</n-text>
                  <n-space size="small">
                    <n-tag 
                      v-for="engine in new Set(vla.quality.map(q => q.engine))" 
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
                        @click="showModalAndSetFields(vla.id, vla.quality)"
                      >
                        Try with Sample
                      </n-button>
                    </template>
                    Test this VLA using sample data
                  </n-tooltip>
                </n-space>
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
  import { ref, onMounted, h, defineComponent } from 'vue'
  import axios from 'axios'
  import { 
    NCard, NButton, NPageHeader, NGrid, NGridItem, 
    NTag, NSpace, NText, NDivider, NTooltip, NEmpty, NIcon, NSpin, useMessage
  } from 'naive-ui'
  import SampleModal from './SampleModal.vue'

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

  const showModalAndSetFields = (id, qua) => {
    sampleModal.value?.show()
    vlaID.value = id
    quality.value = qua
  }

  const data = ref(null)
  const vlaID = ref(null)
  const quality = ref(null)

  const onDataSelected = async (newData) => {
    const body = {
      "exchangeID": "xchg-0001",
      "attesterID": "attester-0000",
      "data": newData,
      "contract": {
        "id": "contract-0001",
        "dataProvider": "/catalog/participants/provider-test-id",
        "vla": {
          "id": vlaID.value,
          "schema": {
            "quality": quality.value
          }
        }
      }
    }

    try {
      const response = await axios.post('/api/attestation', body)
      if (response.status === 200 || response.status === 201) {
        message.success('Attestation submitted successfully!')
      }
    } catch (err) {
      message.error('Failed to submit attestation.')
    } finally {
      vlaID.value = null
      quality.value = null
    }
  }

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
</style>
