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
            <div class="section-row">
              <span class="section-label">Metadata suggestion</span>
              <n-checkbox v-model:checked="applyMetadata" size="small">Fill in the VLA metadata</n-checkbox>
            </div>
            <dl class="metadata-preview" :class="{ unselected: !applyMetadata }">
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
              <article
                v-for="(requirement, index) in draft.requirements"
                :key="`${index}-${requirement.templateId}`"
                class="requirement-card"
                :class="checkTone(index)"
              >
                <div class="requirement-topline">
                  <strong>{{ requirement.template.name }}</strong>
                  <EngineBadge :engine="requirement.template.evaluationMethod?.engine" />
                </div>
                <p>{{ requirement.reason }}</p>
                <TemplateVariables :schema="requirement.template.evaluationMethod?.variableSchema" :values="requirement.model" />
                <div class="check" role="status">
                  <span class="check-pill">{{ checkLabel(index) }}</span>
                  <span v-if="checks[index] && !checks[index].valid && checks[index].details" class="check-details">{{ checks[index].details }}</span>
                </div>
              </article>
            </div>
            <p v-else class="muted">No available template was selected.</p>
            <div v-if="failedCount" class="check-summary">
              <span>{{ failedCount }} requirement{{ failedCount === 1 ? '' : 's' }} will not be attached until {{ failedCount === 1 ? 'it passes' : 'they pass' }} validation.</span>
              <n-button v-if="unavailableCount" size="tiny" secondary :disabled="checking" @click="runChecks">Check again</n-button>
            </div>
          </div>

          <div v-if="draft.missingTemplates.length" class="missing-panel">
            <div class="section-row">
              <strong>Templates to create</strong>
              <span class="count">{{ createdMissing.length }} / {{ draft.missingTemplates.length }} created</span>
            </div>
            <p class="missing-help">Create each template in its own session. Tick it once it is saved, then ask the assistant to check again.</p>
            <ol class="missing-list">
              <li v-for="(item, index) in draft.missingTemplates" :key="index" class="missing-item" :class="{ created: createdMissing.includes(index) }">
                <div class="missing-text">
                  <strong>{{ missingTemplateName(item) }}</strong>
                  <p v-if="item.reason && item.reason !== missingTemplateName(item)">{{ item.reason }}</p>
                </div>
                <div class="missing-actions">
                  <n-button size="small" secondary @click="emit('create-template', item)">Create this template</n-button>
                  <n-checkbox :checked="createdMissing.includes(index)" size="small" @update:checked="toggleCreated(index, $event)">Created</n-checkbox>
                </div>
              </li>
            </ol>
            <div class="recheck">
              <n-button size="small" type="primary" :disabled="!createdMissing.length || busy" @click="recheck">
                Recheck templates
              </n-button>
              <span v-if="!createdMissing.length" class="muted">Tick the templates you have created first.</span>
            </div>
          </div>

          <div class="draft-actions">
            <n-button secondary @click="draft = null">Keep editing</n-button>
            <n-button type="primary" :disabled="!canApply" :loading="checking" @click="apply">{{ applyLabel }}</n-button>
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
import { NAlert, NButton, NCheckbox, NDrawer, NDrawerContent, NInput } from 'naive-ui'
import { askVlaBuilderAssistant, assistantErrorMessage } from '../api/assistant.js'
import { validationTone } from '../api/templates.js'
import EngineBadge from './EngineBadge.vue'
import TemplateVariables from './TemplateVariables.vue'
import {
  checkDraftRequirements,
  createBuilderAssistantContext,
  missingTemplateName,
  normaliseAssistantRequest,
  normaliseVlaAssistantReply,
  passingRequirements,
  recheckRequest
} from '../api/vlaBuilderAssistant.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  context: { type: Object, default: () => ({}) },
  templates: { type: Array, default: () => [] },
  // Reloads the template catalog; awaited before a recheck so templates
  // created in the meantime are known here too.
  refreshTemplates: { type: Function, default: async () => {} }
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
// The last draft the assistant returned, kept after `draft` is cleared for
// a new request so the assistant can build on it.
const lastDraft = ref(null)
// Indices into draft.missingTemplates the author has marked as created.
const createdMissing = ref([])
const busy = computed(() => loading.value || messages.value.some(item => item.revealing))
const metadataEntries = computed(() => Object.entries(draft.value?.metadata || {}).filter(([, value]) => value !== '' && value !== null && value !== undefined && !(Array.isArray(value) && !value.length)))

// Validation verdicts, index-aligned with draft.requirements; `null` while
// a requirement is still being checked.
const checks = ref([])
const checking = computed(() => checks.value.some(check => check === null))
const applyMetadata = ref(false)
let checkRun = 0

const passing = computed(() => passingRequirements(draft.value?.requirements, checks.value))
const failedCount = computed(() => checks.value.filter(check => check && !check.valid).length)
const unavailableCount = computed(() => checks.value.filter(check => check && validationTone(check) === 'unavailable').length)
const includeMetadata = computed(() => applyMetadata.value && metadataEntries.value.length > 0)
const canApply = computed(() => !checking.value && (passing.value.length > 0 || includeMetadata.value))
const applyLabel = computed(() => {
  if (checking.value) return 'Validating…'
  const count = passing.value.length
  const requirements = `${count} requirement${count === 1 ? '' : 's'}`
  if (count && includeMetadata.value) return `Apply ${requirements} and metadata`
  if (includeMetadata.value) return 'Apply metadata'
  return count ? `Apply ${requirements}` : 'Apply to builder'
})

function checkTone (index) {
  const check = checks.value[index]
  return check ? validationTone(check) : 'checking'
}
function checkLabel (index) {
  return { checking: 'Validating…', valid: 'Valid', invalid: 'Invalid', unavailable: 'Could not validate' }[checkTone(index)]
}

async function runChecks () {
  const requirements = draft.value?.requirements || []
  const run = ++checkRun
  checks.value = requirements.map(() => null)
  const results = await checkDraftRequirements(requirements)
  // A newer draft or re-check owns the verdicts now.
  if (run === checkRun) checks.value = results
}

function labelFor (value) {
  return String(value).replace(/[A-Z]/g, letter => ` ${letter}`).replace(/^./, letter => letter.toUpperCase())
}
function formatValue (value) { return Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : String(value) }
function context () { return createBuilderAssistantContext({ ...props.context, draft: lastDraft.value }) }
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
  checks.value = []
  checkRun++
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
    lastDraft.value = normalised
    applyMetadata.value = false
    createdMissing.value = []
    runChecks()
  } catch (cause) {
    error.value = assistantErrorMessage(cause)
  } finally {
    loading.value = false
  }
}
function sendLast () { send(lastRequest.value) }

// The author ticks each missing template once they have created it; nothing
// tracks templates on their behalf. The recheck names the ticked ones and
// hands the assistant its previous draft to complete.
function toggleCreated (index, created) {
  const rest = createdMissing.value.filter(item => item !== index)
  createdMissing.value = created ? [...rest, index] : rest
}

async function recheck () {
  const created = (draft.value?.missingTemplates || []).filter((_, index) => createdMissing.value.includes(index))
  if (!created.length || busy.value) return
  await props.refreshTemplates()
  send(recheckRequest(created))
}
function apply () {
  if (!canApply.value) return
  emit('apply', {
    metadata: includeMetadata.value ? draft.value.metadata : {},
    requirements: passing.value,
    includeMetadata: includeMetadata.value
  })
}
watch(() => props.show, value => { if (!value) error.value = '' })
</script>

<style scoped>
.assistant-body{display:grid;gap:16px;padding-bottom:24px}.drawer-heading{display:flex;align-items:center;gap:10px}.heading-mark,.empty-mark{display:grid;place-items:center;color:#0f766e}.heading-mark{width:30px;height:30px;border:1px solid #99f6e4;border-radius:8px;background:#f0fdfa;font-size:18px}.eyebrow,.section-label{display:block;color:#0f766e;font-size:.6rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}.drawer-heading strong{display:block;margin-top:3px;color:#1e293b;font-size:.88rem}.intro{margin:0;padding-bottom:13px;border-bottom:1px solid #e2e8f0;color:#64748b;font-size:.73rem;line-height:1.5}.conversation{display:grid;gap:12px;max-height:360px;overflow:auto;padding:2px}.empty-conversation{display:grid;justify-items:center;padding:16px 10px;text-align:center}.empty-mark{width:36px;height:36px;margin-bottom:8px;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc;font-size:18px}.empty-conversation strong{color:#334155;font-size:.78rem}.empty-conversation p,.muted{margin:5px 0 0;color:#94a3b8;font-size:.7rem;line-height:1.45}.message{display:grid;gap:4px;justify-items:start}.message.user{justify-items:end}.message-label{color:#94a3b8;font-size:.59rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase}.message p{max-width:92%;margin:0;padding:9px 11px;border:1px solid #e2e8f0;border-radius:4px 11px 11px 11px;background:#f8fafc;color:#475569;font-size:.73rem;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.message.user p{border-color:#bae6fd;border-radius:11px 4px 11px 11px;background:#f0f9ff;color:#164e63}.cursor{display:inline-block;width:2px;height:1em;margin-left:2px;vertical-align:-.15em;background:#0f766e;animation:blink .9s steps(1,end) infinite}.skeleton{display:grid;gap:9px;width:100%;padding:12px;border:1px solid #dbe4ec;border-radius:4px 11px 11px 11px;background:#f8fafc}.skeleton span{display:block;width:88%;height:9px;border-radius:4px;background:#dce5ec;animation:pulse 1.35s ease-in-out infinite}.skeleton span:nth-child(2){width:68%;animation-delay:.08s}.skeleton .short{width:48%}.skeleton div{display:flex;gap:10px}.skeleton div span{width:55%}.assistant-error{font-size:.72rem}.assistant-error p{margin:4px 0 8px}.draft-card{display:grid;gap:13px;padding:15px;border:1px solid #cbd5e1;border-radius:12px;background:#fff}.draft-heading,.section-row,.requirement-topline,.draft-actions{display:flex;align-items:center;justify-content:space-between;gap:10px}.draft-heading h3{margin:3px 0 0;color:#1e293b;font-size:.9rem}.not-saved{padding:3px 6px;border:1px solid #cbd5e1;border-radius:999px;color:#64748b;font-size:.56rem;font-weight:800;text-transform:uppercase}.draft-message{margin:-3px 0 0;color:#475569;font-size:.71rem;line-height:1.5}.preview-section{display:grid;gap:8px}.count{color:#94a3b8;font-size:.65rem;font-weight:800}.metadata-preview{display:grid;grid-template-columns:max-content 1fr;gap:5px 10px;margin:0;padding:10px;border:1px solid #e2e8f0;border-radius:9px;background:#f8fafc;font-size:.68rem}.metadata-preview dt{color:#94a3b8;font-weight:700}.metadata-preview dd{margin:0;color:#334155;overflow-wrap:anywhere}.requirement-list{display:grid;gap:8px}.requirement-card{display:grid;gap:7px;padding:10px;border:1px solid #dbe4ec;border-radius:9px;background:#f8fafc}.requirement-topline strong{min-width:0;color:#334155;font-size:.73rem;overflow-wrap:anywhere}.requirement-card p{margin:0;color:#64748b;font-size:.67rem;line-height:1.4}.requirement-card pre{max-height:130px;overflow:auto;margin:0;padding:8px;border-radius:6px;background:#0f172a;color:#bae6fd;font:500 .62rem/1.5 ui-monospace,monospace;white-space:pre-wrap}.missing-panel{display:grid;gap:7px;padding:10px;border:1px solid #fcd34d;border-radius:9px;background:#fffbeb;color:#78350f;font-size:.69rem}.missing-panel p{margin:0;line-height:1.4}.composer{display:grid;gap:8px;padding:11px;border:1px solid #cbd5e1;border-radius:11px}.composer-label,.composer-footer{display:flex;align-items:center;justify-content:space-between;gap:8px}.composer-label{color:#334155;font-size:.66rem;font-weight:800}.composer-label span:last-child,.composer-footer span{color:#94a3b8;font-size:.6rem;font-weight:500}.composer-footer{align-items:center}.composer-footer :deep(.n-button){font-size:.68rem}.draft-actions :deep(.n-button){font-size:.68rem}@keyframes pulse{0%,100%{opacity:.45}50%{opacity:.95}}@keyframes blink{0%,45%{opacity:1}46%,100%{opacity:0}}@media(prefers-reduced-motion:reduce){.cursor,.skeleton span{animation:none}}
.requirement-card.valid{border-color:#a7f3d0}.requirement-card.invalid{border-color:#fecaca;background:#fef2f2}.requirement-card.unavailable{border-color:#fcd34d;background:#fffbeb}.check{display:grid;gap:4px;justify-items:start}.check-pill{padding:2px 6px;border-radius:999px;background:#e2e8f0;color:#475569;font-size:.56rem;font-weight:800;text-transform:uppercase}.valid .check-pill{background:#d1fae5;color:#047857}.invalid .check-pill{background:#fee2e2;color:#b91c1c}.unavailable .check-pill{background:#fef3c7;color:#92400e}.check-details{color:#7f1d1d;font-size:.64rem;line-height:1.4;white-space:pre-wrap;overflow-wrap:anywhere}.unavailable .check-details{color:#78350f}.check-summary{display:flex;align-items:center;justify-content:space-between;gap:8px;color:#64748b;font-size:.66rem}.metadata-preview.unselected{opacity:.55}
.missing-help{color:#92400e}.missing-list{display:grid;gap:7px;margin:0;padding:0;list-style:none}.missing-item{display:grid;gap:7px;padding:9px;border:1px solid #fde68a;border-radius:8px;background:#fff}.missing-item.created{border-color:#a7f3d0;background:#f0fdf4}.missing-text{display:grid;gap:3px}.missing-text strong{color:#451a03}.missing-text p{color:#78350f}.missing-actions{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}.recheck{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
</style>
