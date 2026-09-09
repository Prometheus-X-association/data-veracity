<template>
  <n-drawer v-model:show="open" placement="right" width="min(94vw, 500px)" class="vla-assistant-drawer">
    <n-drawer-content closable :native-scrollbar="false">
      <template #header>
        <div class="drawer-heading">
          <span class="heading-mark" aria-hidden="true">✦</span>
          <div>
            <span class="eyebrow">VLA builder assistant</span>
            <strong>Describe what the data must guarantee</strong>
          </div>
        </div>
      </template>

      <div class="assistant-body">
        <p class="intro">The assistant uses the sample and available templates to prepare a draft. Nothing is saved until you apply it and create the VLA.</p>

        <section class="conversation" aria-live="polite">
          <div v-if="!messages.length && !loading" class="empty-conversation">
            <span class="empty-mark" aria-hidden="true">✦</span>
            <strong>Start with the data rule</strong>
            <p>Mention the fields, ranges, freshness, or exact shape you need.</p>
          </div>
          <article v-for="(item, index) in messages" :key="`${item.role}-${index}`" class="message" :class="item.role">
            <span class="message-label">{{ item.role === 'user' ? 'You' : 'Assistant' }}</span>
            <p>{{ item.content }}<span v-if="item.revealing" class="cursor" aria-hidden="true"></span></p>
          </article>
          <article v-if="loading" class="message assistant">
            <span class="message-label">Assistant · preparing</span>
            <div class="skeleton" role="status" aria-label="Preparing VLA draft">
              <span></span><span></span><span class="short"></span>
              <div><span></span><span class="short"></span></div>
            </div>
          </article>
        </section>

        <n-alert v-if="error" type="error" :show-icon="false" class="assistant-error">
          <strong>Could not prepare a draft</strong>
          <p>{{ error }}</p>
          <n-button size="small" secondary @click="sendLast">Try again</n-button>
        </n-alert>

        <section v-if="draft" class="draft-card">
          <div class="draft-heading">
            <div>
              <span class="eyebrow">Draft for review</span>
              <h3>Suggested VLA definition</h3>
            </div>
            <span class="not-saved">Not saved</span>
          </div>
          <p class="draft-message">{{ draft.message }}</p>

          <div v-if="metadataEntries.length" class="preview-section">
            <span class="section-label">Metadata suggestion</span>
            <dl class="metadata-preview">
              <template v-for="entry in metadataEntries" :key="entry[0]">
                <dt>{{ labelFor(entry[0]) }}</dt>
                <dd>{{ formatValue(entry[1]) }}</dd>
              </template>
            </dl>
          </div>

          <div class="preview-section">
            <div class="section-row">
              <span class="section-label">Requirements</span>
              <span class="count">{{ draft.requirements.length }}</span>
            </div>
            <div v-if="draft.requirements.length" class="requirement-list">
              <article v-for="requirement in draft.requirements" :key="requirement.templateId" class="requirement-card">
                <div class="requirement-topline">
                  <strong>{{ requirement.template.name }}</strong>
                  <span class="engine">{{ requirement.template.evaluationMethod?.engine }}</span>
                </div>
                <p>{{ requirement.reason }}</p>
                <pre>{{ pretty(requirement.model) }}</pre>
              </article>
            </div>
            <p v-else class="muted">No available template was selected.</p>
          </div>

          <div v-if="draft.missingTemplates.length" class="missing-panel">
            <strong>Some rules need a template</strong>
            <p v-for="(item, index) in draft.missingTemplates" :key="index">{{ item.reason || item.description || 'No matching template is available yet.' }}</p>
            <n-button size="small" secondary @click="emit('create-template', draft.missingTemplates)">Create a template</n-button>
          </div>

          <div class="draft-actions">
            <n-button secondary @click="draft = null">Keep editing</n-button>
            <n-button type="primary" :disabled="!draft.requirements.length" @click="apply">Apply to builder</n-button>
          </div>
        </section>

        <section class="composer">
          <div class="composer-label"><span>Requirement</span><span>{{ input.length }}/1000</span></div>
          <n-input
            v-model:value="input"
            type="textarea"
            maxlength="1000"
            :autosize="{ minRows: 4, maxRows: 8 }"
            :disabled="busy"
            placeholder="For example: every record must have a UTC timestamp and production_kwh between 0 and 100000."
            aria-label="Describe the VLA requirement"
            @keydown.enter.exact.prevent="send()"
          />
          <div class="composer-footer">
            <span>Enter to send · Shift + Enter for a new line</span>
            <n-button type="primary" :loading="loading" :disabled="busy || !input.trim()" @click="send()">Generate draft</n-button>
          </div>
        </section>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { NAlert, NButton, NDrawer, NDrawerContent, NInput } from 'naive-ui'
import { askVlaBuilderAssistant, assistantErrorMessage } from '../api/assistant.js'
import { createBuilderAssistantContext, normaliseAssistantRequest, normaliseVlaAssistantReply } from '../api/vlaBuilderAssistant.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  context: { type: Object, default: () => ({}) },
  templates: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:show', 'apply', 'create-template', 'retry'])

const open = computed({
  get: () => props.show,
  set: value => emit('update:show', value)
})
const input = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([])
const draft = ref(null)
const lastRequest = ref('')
const busy = computed(() => loading.value || messages.value.some(item => item.revealing))
const metadataEntries = computed(() => Object.entries(draft.value?.metadata || {}).filter(([, value]) => value !== '' && value !== null && value !== undefined))

function labelFor (value) {
  return String(value).replace(/[A-Z]/g, letter => ` ${letter}`).replace(/^./, letter => letter.toUpperCase())
}
function formatValue (value) { return Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : String(value) }
function pretty (value) { return JSON.stringify(value, null, 2) }
function context () { return createBuilderAssistantContext(props.context) }
function scrollConversation () { nextTick(() => document.querySelector('.vla-assistant-drawer .conversation')?.scrollTo({ top: 99999, behavior: 'smooth' })) }

async function reveal (message, content) {
  const words = String(content || '').split(/(\s+)/)
  message.revealing = true
  for (const word of words) {
    message.content += word
    scrollConversation()
    await new Promise(resolve => setTimeout(resolve, word.trim() ? 22 : 8))
  }
  message.revealing = false
}

async function send (value) {
  const request = normaliseAssistantRequest(value ?? input.value)
  if (!request || busy.value) return
  input.value = ''
  lastRequest.value = request
  error.value = ''
  draft.value = null
  messages.value.push({ role: 'user', content: request, revealing: false })
  loading.value = true
  try {
    const conversation = messages.value.slice(0, -1).map(item => ({ role: item.role, content: item.content }))
    const response = await askVlaBuilderAssistant({ message: request, conversation, builderContext: context() })
    const normalised = normaliseVlaAssistantReply(response, props.templates)
    const assistantMessage = { role: 'assistant', content: '', revealing: true }
    messages.value.push(assistantMessage)
    await reveal(assistantMessage, normalised.message)
    draft.value = normalised
  } catch (cause) {
    error.value = assistantErrorMessage(cause)
  } finally {
    loading.value = false
  }
}
function sendLast () { send(lastRequest.value) }
function apply () { if (draft.value?.requirements.length) emit('apply', draft.value) }
watch(() => props.show, value => { if (!value) error.value = '' })
</script>

<style scoped>
.assistant-body{display:grid;gap:16px;padding-bottom:24px}.drawer-heading{display:flex;align-items:center;gap:10px}.heading-mark,.empty-mark{display:grid;place-items:center;color:#0f766e}.heading-mark{width:30px;height:30px;border:1px solid #99f6e4;border-radius:8px;background:#f0fdfa;font-size:18px}.eyebrow,.section-label{display:block;color:#0f766e;font-size:.6rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}.drawer-heading strong{display:block;margin-top:3px;color:#1e293b;font-size:.88rem}.intro{margin:0;padding-bottom:13px;border-bottom:1px solid #e2e8f0;color:#64748b;font-size:.73rem;line-height:1.5}.conversation{display:grid;gap:12px;max-height:360px;overflow:auto;padding:2px}.empty-conversation{display:grid;justify-items:center;padding:16px 10px;text-align:center}.empty-mark{width:36px;height:36px;margin-bottom:8px;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc;font-size:18px}.empty-conversation strong{color:#334155;font-size:.78rem}.empty-conversation p,.muted{margin:5px 0 0;color:#94a3b8;font-size:.7rem;line-height:1.45}.message{display:grid;gap:4px;justify-items:start}.message.user{justify-items:end}.message-label{color:#94a3b8;font-size:.59rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase}.message p{max-width:92%;margin:0;padding:9px 11px;border:1px solid #e2e8f0;border-radius:4px 11px 11px 11px;background:#f8fafc;color:#475569;font-size:.73rem;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.message.user p{border-color:#bae6fd;border-radius:11px 4px 11px 11px;background:#f0f9ff;color:#164e63}.cursor{display:inline-block;width:2px;height:1em;margin-left:2px;vertical-align:-.15em;background:#0f766e;animation:blink .9s steps(1,end) infinite}.skeleton{display:grid;gap:9px;width:100%;padding:12px;border:1px solid #dbe4ec;border-radius:4px 11px 11px 11px;background:#f8fafc}.skeleton span{display:block;width:88%;height:9px;border-radius:4px;background:#dce5ec;animation:pulse 1.35s ease-in-out infinite}.skeleton span:nth-child(2){width:68%;animation-delay:.08s}.skeleton .short{width:48%}.skeleton div{display:flex;gap:10px}.skeleton div span{width:55%}.assistant-error{font-size:.72rem}.assistant-error p{margin:4px 0 8px}.draft-card{display:grid;gap:13px;padding:15px;border:1px solid #cbd5e1;border-radius:12px;background:#fff}.draft-heading,.section-row,.requirement-topline,.draft-actions{display:flex;align-items:center;justify-content:space-between;gap:10px}.draft-heading h3{margin:3px 0 0;color:#1e293b;font-size:.9rem}.not-saved{padding:3px 6px;border:1px solid #cbd5e1;border-radius:999px;color:#64748b;font-size:.56rem;font-weight:800;text-transform:uppercase}.draft-message{margin:-3px 0 0;color:#475569;font-size:.71rem;line-height:1.5}.preview-section{display:grid;gap:8px}.count{color:#94a3b8;font-size:.65rem;font-weight:800}.metadata-preview{display:grid;grid-template-columns:max-content 1fr;gap:5px 10px;margin:0;padding:10px;border:1px solid #e2e8f0;border-radius:9px;background:#f8fafc;font-size:.68rem}.metadata-preview dt{color:#94a3b8;font-weight:700}.metadata-preview dd{margin:0;color:#334155;overflow-wrap:anywhere}.requirement-list{display:grid;gap:8px}.requirement-card{display:grid;gap:7px;padding:10px;border:1px solid #dbe4ec;border-radius:9px;background:#f8fafc}.requirement-topline strong{min-width:0;color:#334155;font-size:.73rem;overflow-wrap:anywhere}.engine{padding:3px 6px;border:1px solid #a7f3d0;border-radius:5px;color:#0f766e;font-size:.56rem;font-weight:800}.requirement-card p{margin:0;color:#64748b;font-size:.67rem;line-height:1.4}.requirement-card pre{max-height:130px;overflow:auto;margin:0;padding:8px;border-radius:6px;background:#0f172a;color:#bae6fd;font:500 .62rem/1.5 ui-monospace,monospace;white-space:pre-wrap}.missing-panel{display:grid;gap:7px;padding:10px;border:1px solid #fcd34d;border-radius:9px;background:#fffbeb;color:#78350f;font-size:.69rem}.missing-panel p{margin:0;line-height:1.4}.composer{display:grid;gap:8px;padding:11px;border:1px solid #cbd5e1;border-radius:11px}.composer-label,.composer-footer{display:flex;align-items:center;justify-content:space-between;gap:8px}.composer-label{color:#334155;font-size:.66rem;font-weight:800}.composer-label span:last-child,.composer-footer span{color:#94a3b8;font-size:.6rem;font-weight:500}.composer-footer{align-items:center}.composer-footer :deep(.n-button){font-size:.68rem}.draft-actions :deep(.n-button){font-size:.68rem}@keyframes pulse{0%,100%{opacity:.45}50%{opacity:.95}}@keyframes blink{0%,45%{opacity:1}46%,100%{opacity:0}}@media(prefers-reduced-motion:reduce){.cursor,.skeleton span{animation:none}}
</style>
