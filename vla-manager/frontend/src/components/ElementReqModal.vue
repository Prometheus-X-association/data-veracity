<template>
    <dialog 
      ref="dialog"
      class="modern-modal"
      @click="handleBackdropClick"
    >
      <div class="modal-content">
        <header>
          <h3>Add Element-Level Requirement</h3>
        </header>

        <section class="modal-body">
          <label for="fragment">Choose a fragment:</label>
          <select v-model="chosenFragment" id="fragment">
            <option v-for="item in fragmentOptions" :key="item" :value="item">
              {{ item.name }} {{ item.description !== "" ? `- ${item.description}` : "" }}
            </option>
          </select>

          <form 
            v-if="chosenFragment !== null"
            class="req-form"
          >
            <template v-if="chosenFragment.evaluationMethod.variableSchema.properties.property">
              <label for="element">Element:</label>
            <input id="element" type="text" :disabled="true" :value="element" />
            </template>
            
            <template v-for="(value, key) in chosenFragment.evaluationMethod.variableSchema.properties" :key="key">
              <template v-if="key !== 'property'">
                <label :for="key">{{ capitalize(key) }}</label>
                <template v-if="key === 'schema'">
                  <textarea 
                    :id="key" 
                    v-model="values[key]" 
                    rows="6"
                    @input="updateSchemaJSON(key)">
                  </textarea>
                  <vue-json-pretty
                    :data="schemaJSON"
                    :show-double-quotes="false"
                    :show-length="false"
                    root-path=""
                    :virtual="true"
                   />
                </template>
                <template v-else>
                  <template v-if="value.enum">
                    <select :id="key" v-model="values[key]" @input="convertType(value.type, key)">
                      <option v-for="v in value.enum" :value="v">{{ v }}</option>
                    </select>
                  </template>
                  <template v-else>
                    <input :id="key" :type="value.type" v-model="values[key]" @input="convertType(value.type, key)" />
                  </template>
                </template>
              </template>
            </template>
          </form>

          <!--
          <form
            v-if="chosenFragment === 'ge-value-between'"
            class="req-form"
          >
            <label for="element">Element:</label>
            <input id="element" type="text" :disabled="true" :value="element" />
            <label for="minValue">Minimum value:</label>
            <input id="minValue" v-model="minValue" type="text" />
            <label for="maxValue">Maximum value:</label>
            <input id="maxValue" v-model="maxValue" type="text" />
          </form>

          <form
            v-else-if="chosenFragment === 'jq-simple-relation'"
            class="req-form"
          >
            <label for="element">Element:</label>
            <input id="element" type="text" :disabled="true" :value="element" />
            <label for="relOp">Relational operator</label>
            <select id="relOp" v-model="relOp">
              <option value="==">==</option>
              <option value="&lt;">&lt;</option>
              <option value="&lt;=">&lt;=</option>
              <option value="&gt;">&gt;</option>
              <option value="&gt;=">&gt;=</option>
            </select>
            <label for="otherOperand">Other operand:</label>
            <input id="otherOperand" v-model="otherOperand" type="text" />
          </form>
          -->
        </section>
        
        <footer>
          <button
            @click="addRequirement"
            class="add-button"
            :disabled="chosenFragment === null"
          >
            Add Requirement
          </button>
        </footer>
      </div>
    </dialog>
</template>

<script setup>
  import axios from 'axios'
  import { ref } from 'vue'
  import { watch, reactive, toRaw } from 'vue'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'

  const dialog = ref(null)

  const fragmentOptions = ref([])
  const values = reactive({})

  const schemaJSON = ref({})

  const chosenFragment = ref(null)

  watch(chosenFragment, (newChosenFragment) => {
    if(newChosenFragment) {
      schemaJSON.value = {}
      for(const key in values) {
        delete values[key]
      }
      for(const key in newChosenFragment.evaluationMethod.variableSchema.properties) {
        if(key === 'property') {
          values[key] = props.element
        } else {
          values[key] = ""
        }
      }
    }
  })

  const capitalize = str => str && typeof str === "string" && str.length >= 1 ? str.charAt(0).toUpperCase() + str.slice(1) : "" 

  const convertType = (type, key) => {
    switch(type) {
      case "number":
        values[key] = Number(values[key])
        break
      case "boolean":
        values[key] = values[key] === "true"
        break
    }
  }

  const updateSchemaJSON = (key) => {
    try {
      schemaJSON.value = JSON.parse(values[key])
    } catch (err) {
      schemaJSON.value = {}
    }
  }

  const showModal = async () => {
    try {
      const res = await axios.get("/api/template")
      const json = await res.data

      if(Array.isArray(json)) {
        fragmentOptions.value = json
      }
    } catch (err) {}


    dialog.value?.showModal()
  }

  const handleBackdropClick = (e) => {
    if (e.target === dialog.value) {
      chosenFragment.value = null 
      dialog.value?.close()
    }
  }

  const emit = defineEmits(['req-added'])
  const props = defineProps(['element'])
  defineExpose({ show: showModal })

  const addRequirement = async () => {
    const rawValues = toRaw(values)
    const template = {}
    const model = {}

    for(const key in rawValues) {
      model[key] = rawValues[key]
    }

    template["id"] = chosenFragment.value.id
    template["model"] = model    

    emit('req-added', template)

    for(const key in values) {
        delete values[key]
    }
    /*try {
      const res = await axios.get(`/api/template/${chosenFragment.value.id}/render`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(toRaw(values))
      })

      const data = await res.data
      console.log(data)

      const emitData = {
        data_quality_type: 'hu.bme.mit.ftsrg.odcs.model.quality.DataQualityCustom',
        engine: data.engine,
        implementation: data.implementation
      }

      emit('req-added', emitData)
    } catch (err) {}
    if (chosenFragment.value === 'ge-value-between') {
      emit('req-added', {
        data_quality_type: 'hu.bme.mit.ftsrg.odcs.model.quality.DataQualityCustom',
        engine: 'greatExpectations',
        implementation: `type: ExpectColumnValuesToBeBetween\nkwargs:\n  column: ${props.element.substring(1)}\n  min_value: '${minValue.value}'\n  max_value: '${maxValue.value}'`,
      })
    } else if (chosenFragment.value === 'jq-simple-relation') {
      emit('req-added', {
        data_quality_type: 'hu.bme.mit.ftsrg.odcs.model.quality.DataQualityCustom',
        engine: 'jq',
        implementation: `${props.element} ${relOp.value} ${otherOperand.value}`,
      })
    } else {
      console.log('unknown fragment')
    }*/

    chosenFragment.value = null
    dialog.value?.close()
  }
</script>

<style scoped>
  .modern-modal::backdrop {
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    animation: backdropFadeIn 0.3s ease-out;
  }
  
  dialog {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    max-width: 50vw;
    max-height: 90vh;
    border: none;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    animation: dialogSlideIn 0.3s ease-out;
  }
  
  h3 {
    margin: 0;
  }

  .req-form {
    display: flex;
    flex-direction: column;
    gap: .2rem;
  }
  
  .modal-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 24px 0;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 16px;
    margin-bottom: 20px;
  }
  
  .modal-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }
  
  .modal-body {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  footer {
    display: flex;
    gap: 1rem;
    align-items: center;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .add-button {
    background: #08c41e;
    font-weight: bold;
  }
  
  /* Animations */
  @keyframes dialogSlideIn {
    from {
      opacity: 0;
      transform: scale(0.95) translateY(-10px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }
  
  @keyframes backdropFadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  
  /* Responsive adjustments */
  @media (max-width: 640px) {
    .modern-modal {
      width: 95vw;
    }
    
    .modal-header,
    .modal-body,
    .modal-footer {
      padding-left: 16px;
      padding-right: 16px;
    }
    
    .modal-footer {
      flex-direction: column-reverse;
    }
    
    .btn-primary,
    .btn-secondary {
      width: 100%;
    }
  }
</style>
