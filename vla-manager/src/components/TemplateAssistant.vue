<template>
  <div>
    <n-button secondary @click="open = true">Design with AI</n-button>

    <n-drawer v-model:show="open" placement="right" :width="440">
      <n-drawer-content title="Template design assistant" closable>
        <div class="assistant-intro">
          Describe the quality requirement in plain language. The assistant will prepare a draft for your review.
        </div>

        <div class="conversation" aria-live="polite">
          <div v-for="(item, index) in messages" :key="`${item.role}-${index}`" class="message" :class="item.role">
            <span class="message-role">{{ item.role === 'user' ? 'You' : 'Assistant' }}</span>
            <p>{{ item.content }}</p>
          </div>
          <n-empty v-if="!messages.length" description="No messages yet" size="small" />
        </div>

        <n-alert v-if="error" type="error" class="assistant-error" closable @close="error = ''">
          {{ error }}
        </n-alert>

        <n-input
          v-model:value="input"
          type="textarea"
          :autosize="{ minRows: 3, maxRows: 7 }"
          placeholder="For example: require every xAPI statement to contain an actor, verb, and object."
          :disabled="loading"
          @keydown.enter.exact.prevent="send"
        />
        <div class="assistant-actions">
          <n-button type="primary" :loading="loading" :disabled="!input.trim()" @click="send">Send</n-button>
          <n-button :disabled="loading" @click="clear">Clear</n-button>
        </div>

        <n-card v-if="proposal" title="Draft proposal" size="small" class="proposal-card">
          <p class="proposal-note">Review this proposal, then apply it to the editor. It is not saved automatically.</p>
          <pre>{{ JSON.stringify(proposal, null, 2) }}</pre>
          <n-button type="primary" block @click="apply">Apply proposal to editor</n-button>
          <div v-if="examples" class="examples">
            <n-divider>Examples</n-divider>
            <pre>{{ JSON.stringify(examples, null, 2) }}</pre>
          </div>
        </n-card>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NAlert, NButton, NCard, NDrawer, NDrawerContent, NDivider, NEmpty, NInput } from 'naive-ui'
import { askTemplateAssistant, assistantErrorMessage } from '../api/assistant.js'

const props = defineProps({ template: { type: Object, default: null } })
const emit = defineEmits(['apply'])
const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([])
const proposal = ref(null)
const examples = ref(null)

function clone (value) {
  return value == null ? null : JSON.parse(JSON.stringify(value))
}

async function send () {
  const message = input.value.trim()
  if (!message || loading.value) return
  messages.value.push({ role: 'user', content: message })
  input.value = ''
  loading.value = true
  error.value = ''
  try {
    const response = await askTemplateAssistant({
      message,
      conversation: messages.value.slice(0, -1),
      currentTemplate: clone(props.template)
    })
    messages.value.push({ role: 'assistant', content: response.message })
    proposal.value = response.proposal || null
    examples.value = response.examples || null
  } catch (cause) {
    error.value = assistantErrorMessage(cause)
  } finally {
    loading.value = false
  }
}

function clear () {
  messages.value = []
  proposal.value = null
  examples.value = null
  error.value = ''
}

function apply () {
  if (!proposal.value) return
  emit('apply', clone(proposal.value))
}
</script>

<style scoped>
.assistant-intro{margin-bottom:16px;color:#64748b;font-size:.78rem;line-height:1.5}.conversation{display:grid;gap:10px;max-height:300px;overflow:auto;margin-bottom:14px}.message{padding:10px 12px;border-radius:8px;background:#f8fafc}.message.user{background:#eff6ff}.message-role{display:block;color:#64748b;font-size:.64rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.message p{margin:4px 0 0;color:#334155;font-size:.76rem;line-height:1.45;white-space:pre-wrap}.assistant-error{margin-bottom:12px}.assistant-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:10px}.proposal-card{margin-top:18px}.proposal-note{margin:0 0 10px;color:#64748b;font-size:.72rem;line-height:1.45}.proposal-card pre{max-height:250px;overflow:auto;margin:0 0 12px;padding:10px;border-radius:6px;background:#0f172a;color:#e2e8f0;font-size:.66rem;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere}.examples{margin-top:12px}.examples :deep(.n-divider){margin:12px 0}.examples pre{max-height:170px;margin-bottom:0}
</style>
