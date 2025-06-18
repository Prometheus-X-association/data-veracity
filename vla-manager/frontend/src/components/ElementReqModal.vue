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
            <option value="ge-value-between">GreatExpetations: Value between</option>
            <option value="jq-simple-relation">jq: Simple numeric relation</option>
          </select>

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
  import { ref } from 'vue'
  import FileSelector from './FileSelector.vue'

  const dialog = ref(null)
  const chosenFragment = ref(null)

  const minValue = ref(null)
  const maxValue = ref(null)

  const relOp = ref(null)
  const otherOperand = ref(null)

  const showModal = async () => dialog.value?.showModal()

  const handleBackdropClick = (e) => {
    if (e.target === dialog.value) dialog.value?.close()
  }

  const emit = defineEmits(['req-added'])
  const props = defineProps(['element'])
  defineExpose({ show: showModal })

  const addRequirement = () => {
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
    }

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
