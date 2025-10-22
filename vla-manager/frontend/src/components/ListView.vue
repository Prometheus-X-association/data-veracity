<template>
  <SampleModal v-model="data" ref="sampleModal" @update:modelValue="onDataSelected"/>
  <div class="content">
    <header>
      <h2>View VLAs</h2>
      <RouterLink to="/create"><button>Create new VLA</button></RouterLink>
    </header>
    <div class="main-part">
      <div v-for="vla in vlas">
        <n-card :title="vla.id">
          <p>Description: {{ vla.description }}</p>
          <p>Engines:</p>
          <ul>
            <div v-for="engine in new Set(vla.quality.map(q => q.engine))">
              <li>{{ engine }}</li>
            </div>
          </ul>
          <template #action>
            <button
              @click="showModalAndSetID(vla.id)"
              class="add-button">
              Try 
            </button>
          </template>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import { NCard } from 'naive-ui'
  import SampleModal from './SampleModal.vue'

  const vlas = ref([])

  const sampleModal = ref(null)

  const showModalAndSetID = (id) => {
    sampleModal.value?.show()
    vlaID.value = id
  }

  const data = ref(null)

  const vlaID = ref(null)

  const onDataSelected = async (newData) => {
    const body = {
      "exchangeID": "xchg-0001",
      "attesterID": "attester-0000",
      "data": newData,
      "contract": {
        "id": "contract-0001",
        "vla": {
          "id": vlaID.value
        }
      }
    }

    try {
      const response = await axios.post('/api/attestation', body)
      console.log({
        "status": response.status,
        "data": response.data
      })
    } catch (err) {}

    vlaID.value = null
  }

  onMounted(async () => {
    const response = await axios.get('/api/vla')
    vlas.value = response.data
  })
</script>

<style scoped>
  h2 {
    justify-self: stretch;
    border-top: 4px solid #e08b1b;
    border-bottom: 4px solid #e08b1b;
    padding: 1rem;
    text-align: center;
    margin: 0;
    margin-bottom: 1rem;
  }

  .content {
    flex-grow: 1;
    flex-direction: column;
    display: flex;
    padding: 1rem;
    gap: 1rem;
  }

  .main-part {
    flex-grow: 1;
    display: flex;
    gap: 1rem;
  }
</style>
