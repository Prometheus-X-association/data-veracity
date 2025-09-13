<template>
  <SampleModal v-model="sampleData" ref="sampleModal" />
  <ElementReqModal
    :element="lastPath"
    ref="elementReqModal"
    @req-added="handleReqAdded"
  />
  <GenericReqModal
    ref="genericReqModal"
    @req-added="handleReqAdded"
  />
  <div class="content">
    <header>
      <h2>Create a new VLA</h2>
    </header>
    <div class="main-part">
      <button
        v-if="sampleData === null"
        @click="showSampleModal"
        class="add-button"
      >
        Add sample data
      </button>

      <div v-if="sampleData !== null" class="editor-area">
        <section class="column">
          <h3>Sample data structure</h3>
          <vue-json-pretty
            :data="sampleData"
            :showDoubleQuotes="false"
            :showLength="true"
            rootPath=""
            :virtual="true"
            :height="600"
            @node-click="onNodeClick"
          />
        </section>

        <section class="column toolbox">
          <h3>Toolbox</h3>

          <div class="element-req-box">
            <p
              v-if="lastPath === null"
              class="json-selection"
              style="font-style:italic"
            >
              Select a JSON element…
            </p>
            <p
              v-else
              class="json-selection"
            >
              {{ lastPath }}
            </p>
            <button
              @click="showElementReqModal"
              :disabled="lastPath === null"
            >
              Add requirement for data element
            </button>
          </div>

          <button @click="showGenericReqModal">
            Add generic requirement
          </button>
        </section>

        <section class="column fragments">
          <h3>List of Fragments</h3>
          <div v-for="frag in fragments" class="fragment">
            <vue-json-pretty :data="frag" />
          </div>
        </section>
      </div>
    </div>
    <footer>
      <button
        @click="handleCreateVLA"
        class="final-button"
        :disabled="sampleData === null"
      >
        Create VLA
      </button>
    </footer>
  </div>
</template>

<script setup>
  import { ref } from 'vue'
  import { toRaw } from 'vue'
  import { useRouter } from 'vue-router'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import axios from 'axios'

  import SampleModal from './SampleModal.vue'
  import ElementReqModal from './ElementReqModal.vue'
  import GenericReqModal from './GenericReqModal.vue'

  const sampleModal = ref(null)
  const elementReqModal = ref(null)
  const genericReqModal = ref(null)

  const sampleData = ref(null)
  const lastPath = ref(null)
  const fragments = ref([])

  const showSampleModal = () => sampleModal.value?.show()
  const showElementReqModal = () => elementReqModal.value?.show()
  const showGenericReqModal = () => genericReqModal.value?.show()

  const onNodeClick = (node) => lastPath.value = node.path

  const handleReqAdded = (req) => {
    fragments.value.push(req)
  }

  const router = useRouter()

  const handleCreateVLA = async () => {
    console.log("posting")
    const body = {
      description: "Data is recent and valid",
      schema: {
        properties: {
          timestamp: {
            type: "string"
          },
          result: {
            type: "integer"
          }
        }
      },
      qualityTemplates: [...toRaw(fragments.value)]
    }

    console.log(JSON.stringify(body))
    try {
      await axios.post('http://localhost:9091/vla/from-templates', body)
    } catch (err) {}
    alert(`Created VLA from ${fragments.value.length} fragments`)
    router.push({ path: "/list" })
  }
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
  }

  .main-part {
    flex-grow: 1;
    display: flex;
  }

  .add-button {
    font-size: 2rem;
    align-self: center;
    margin: auto;
  }

  .editor-area {
    flex-grow: 1;
    display: flex;
    justify-content: space-between;
  }

  .column {
    width: 30vw;
  }

  .toolbox {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }

  .fragments {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .json-selection {
    font-family: monospace;
    font-size: 1.25rem;
    background: #ccc;
    padding: 1rem;
    margin: 0 2rem;
    flex-grow: 1;
  }

  .fragment {
    padding: 1rem;
    border: 2px solid black;
    border-radius: 12px;
  }

  footer {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .final-button {
    width: 15rem;
    background-color: #e08b1b;
    font-size: 1.5rem;
  }

  .element-req-box {
    align-self: stretch;
    text-align: center;
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    align-items: center;
  }
</style>
