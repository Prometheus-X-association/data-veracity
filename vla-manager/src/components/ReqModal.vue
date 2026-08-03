<template>
  <n-modal
    v-model:show="showModalFlag"
    preset="card"
    title="Add Requirement"
    class="req-modal"
    size="huge"
    :style="{ width: '600px', maxWidth: '95vw' }"
  >
    <div class="modal-body">
      <n-form :model="values" label-placement="top" size="large">
        <n-form-item label="Choose a fragment:" path="chosenFragment">
          <n-select
            v-model:value="selectedFragmentId"
            :options="fragmentOptions.map(f => ({ label: f.name, value: f.id }))"
            placeholder="Select a requirement template..."
            @update:value="handleFragmentSelect"
          />
        </n-form-item>

        <template v-if="chosenFragment">
          <n-alert v-if="chosenFragment.description" type="info" :show-icon="false" class="mb-4">
            {{ chosenFragment.description }}
          </n-alert>

          <template v-if="chosenFragment.evaluationMethod?.variableSchema?.properties?.property">
            <n-form-item label="Element:">
              <n-input disabled :value="element" />
            </n-form-item>
          </template>

          <template v-if="chosenFragment.evaluationMethod?.variableSchema?.properties">
            <template v-for="(value, key) in chosenFragment.evaluationMethod.variableSchema.properties" :key="key">
              <n-form-item v-if="key !== 'property'" :label="capitalize(key)" :path="key">

                <template v-if="key === 'schema'">
                  <div class="w-full">
                    <n-input
                      v-model:value="values[key]"
                      type="textarea"
                      placeholder="Enter JSON schema..."
                      :autosize="{ minRows: 4, maxRows: 8 }"
                      @input="updateSchemaJSON(key)"
                    />
                    <div class="json-preview mt-2" v-if="schemaJSON && Object.keys(schemaJSON).length > 0">
                      <vue-json-pretty
                        :data="schemaJSON"
                        :show-double-quotes="false"
                        :show-length="false"
                        root-path=""
                        :virtual="true"
                      />
                    </div>
                  </div>
                </template>

                <template v-else-if="value.enum">
                  <n-select
                    v-model:value="values[key]"
                    :options="value.enum.map(e => ({ label: e, value: e }))"
                    @update:value="convertType(value.type, key)"
                  />
                </template>

                <template v-else-if="value.type === 'boolean'">
                  <n-switch v-model:value="values[key]" />
                </template>

                <template v-else-if="value.type === 'number' || value.type === 'integer'">
                  <n-input-number v-model:value="values[key]" class="w-full" />
                </template>

                <template v-else>
                  <n-input v-model:value="values[key]" @input="convertType(value.type, key)" />
                </template>

              </n-form-item>
            </template>
          </template>
        </template>
      </n-form>

      <div
        v-if="validationResult"
        class="validation-feedback"
        :class="validationTone(validationResult)"
        role="status"
      >
        <strong>{{ validationResult.reason }}</strong>
        <p v-if="validationResult.details">{{ validationResult.details }}</p>
        <details v-if="validationResult.implementation">
          <summary>Rendered implementation</summary>
          <pre>{{ validationResult.implementation }}</pre>
        </details>
      </div>
    </div>

    <template #footer>
      <n-space justify="end">
        <n-button @click="showModalFlag = false">Cancel</n-button>
        <n-button @click="validateRequirement" :disabled="!chosenFragment || validating">
          Validate
        </n-button>
        <n-button type="primary" @click="addRequirement" :disabled="!chosenFragment || validating">
          {{ validating ? 'Validating…' : 'Add Requirement' }}
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup>
  import axios from 'axios'
  import { ref, watch, reactive, toRaw } from 'vue'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'
  import {
    NModal, NForm, NFormItem, NSelect, NInput, NInputNumber,
    NSwitch, NSpace, NButton, NAlert
  } from 'naive-ui'
  import {
    coerceTemplateValue,
    validateTemplate,
    validationFailureFromError,
    validationTone
  } from '../api/templates.js'

  const showModalFlag = ref(false)

  const fragmentOptions = ref([])
  const values = reactive({})

  const schemaJSON = ref({})
  const chosenFragment = ref(null)
  const selectedFragmentId = ref(null)
  const validating = ref(false)
  const validationResult = ref(null)

  const handleFragmentSelect = (val) => {
    chosenFragment.value = fragmentOptions.value.find(f => f.id === val)
  }

  watch(chosenFragment, (newChosenFragment) => {
    if(newChosenFragment) {
      validationResult.value = null
      schemaJSON.value = {}
      for(const key in values) {
        delete values[key]
      }
      for(const key in newChosenFragment.evaluationMethod?.variableSchema?.properties || {}) {
        if(key === 'property') {
          values[key] = props.element
        } else if (newChosenFragment.evaluationMethod?.variableSchema?.properties?.[key]?.type === 'boolean') {
          values[key] = false
        } else {
          values[key] = ""
        }
      }
    }
  })

  const capitalize = str => str && typeof str === "string" && str.length >= 1 ? str.charAt(0).toUpperCase() + str.slice(1) : ""

  const convertType = (type, key) => {
    values[key] = coerceTemplateValue(type, values[key])
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
    } catch (err) {
      console.error(err)
    }

    // Reset state
    chosenFragment.value = null
    selectedFragmentId.value = null
    validationResult.value = null
    for(const key in values) {
      delete values[key]
    }
    showModalFlag.value = true
  }

  const emit = defineEmits(['req-added'])
  const props = defineProps(['element'])
  defineExpose({ show: showModal })

  const currentModel = () => {
    const rawValues = toRaw(values)
    const model = {}

    for(const key in rawValues) {
      model[key] = rawValues[key]
    }

    if (props.element && chosenFragment.value?.evaluationMethod?.variableSchema?.properties?.property) {
      let propPath = props.element.trim()
      if (!propPath.startsWith('.')) {
        propPath = '.' + propPath
      }
      model.property = propPath
    }

    return model
  }

  // Validating and adding both go through here, so the author can check a
  // requirement as many times as they like before committing to it.
  const runValidation = async (model) => {
    validating.value = true
    validationResult.value = null
    try {
      validationResult.value = await validateTemplate(chosenFragment.value.id, model)
    } catch (err) {
      validationResult.value = validationFailureFromError(err)
    } finally {
      validating.value = false
    }

    return validationResult.value
  }

  const validateRequirement = async () => {
    await runValidation(currentModel())
  }

  const addRequirement = async () => {
    const model = currentModel()

    if (!(await runValidation(model)).valid) return

    const req = {
      data: {
        id: chosenFragment.value.id,
        model
      },
      requirement: chosenFragment.value
    }

    emit('req-added', req)

    for(const key in values) {
        delete values[key]
    }
    chosenFragment.value = null
    selectedFragmentId.value = null
    showModalFlag.value = false
  }
</script>

<style scoped>
  .modal-body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding-top: 8px;
  }

  .validation-feedback {
    border: 1px solid;
    border-radius: 8px;
    display: grid;
    gap: .4rem;
    padding: .8rem;
  }

  .validation-feedback.valid {
    background: #edf9ef;
    border-color: #6eb878;
  }

  .validation-feedback.invalid {
    background: #fff0f0;
    border-color: #d86a6a;
  }

  .validation-feedback.unavailable {
    background: #fff8e8;
    border-color: #d49b35;
  }

  .validation-feedback p,
  .validation-feedback pre {
    margin: 0;
  }

  .validation-feedback pre {
    overflow-x: auto;
    white-space: pre-wrap;
  }

  .mb-4 {
    margin-bottom: 16px;
  }

  .mt-2 {
    margin-top: 8px;
  }

  .w-full {
    width: 100%;
  }

  .json-preview {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    padding: 8px;
    max-height: 200px;
    overflow-y: auto;
  }
</style>
