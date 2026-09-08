<template>
  <div class="assistant-launcher">
    <n-button class="assistant-trigger" secondary @click="open = true">
      <template #icon><n-icon><SparkleIcon /></n-icon></template>
      Design with AI
    </n-button>
  </div>

  <n-drawer v-model:show="open" placement="right" width="min(92vw, 480px)" class="assistant-drawer">
    <n-drawer-content closable :native-scrollbar="false">
      <template #header>
        <div class="assistant-drawer-title">
          <div class="assistant-title-mark"><SparkleIcon /></div>
          <div>
            <span class="assistant-kicker">Template assistant</span>
            <strong>Design a requirement</strong>
          </div>
        </div>
      </template>

      <div class="assistant-content">
        <p class="assistant-intro">Describe the quality rule in plain language. The assistant will prepare a draft for your review. Nothing is saved automatically.</p>

        <section ref="conversationEl" class="conversation" aria-live="polite" aria-label="Assistant conversation">
          <div v-if="!messages.length && !loading" class="conversation-empty">
            <div class="empty-icon"><SparkleIcon /></div>
            <strong>Start with the rule you need</strong>
            <p>Mention the fields, values, freshness, or schema that your data should satisfy.</p>
          </div>

          <article v-for="(item, index) in messages" :key="item.role + '-' + index" class="message" :class="[item.role, { 'is-revealing': item.id === revealingMessageId }]">
            <div class="message-avatar" aria-hidden="true">
              <UserIcon v-if="item.role === 'user'" />
              <SparkleIcon v-else />
            </div>
            <div class="message-content">
              <div class="message-meta">
                <span>{{ item.role === 'user' ? 'You' : 'VLA assistant' }}</span>
                <span v-if="item.role === 'assistant'" class="ai-label">AI</span>
              </div>
              <p><span>{{ item.content }}</span><span v-if="item.id === revealingMessageId" class="typing-cursor" aria-hidden="true"></span></p>
            </div>
          </article>

          <article v-if="loading" class="message assistant is-generating">
            <div class="message-avatar assistant-avatar" aria-hidden="true"><SparkleIcon /></div>
            <div class="message-content">
              <div class="message-meta"><span>VLA assistant</span><span class="generating-label"><span class="generating-dot"></span> Generating</span></div>
              <div class="skeleton-card" role="status" aria-label="Generating draft">
                <div class="skeleton-heading"><span class="skeleton-avatar"></span><span class="skeleton-line skeleton-title"></span></div>
                <span class="skeleton-line skeleton-wide"></span>
                <span class="skeleton-line skeleton-medium"></span>
                <div class="skeleton-row"><span class="skeleton-line"></span><span class="skeleton-line skeleton-short"></span></div>
                <div class="skeleton-row"><span class="skeleton-line skeleton-short"></span><span class="skeleton-line"></span></div>
              </div>
            </div>
          </article>
        </section>

        <n-alert v-if="error" type="error" class="assistant-error" closable @close="error = ''">
          <strong>Assistant unavailable</strong>
          <div>{{ error }}</div>
        </n-alert>

        <div class="composer">
          <div class="composer-label"><span>Describe your requirement</span><span>{{ input.length }}/1000</span></div>
          <n-input
            v-model:value="input"
            class="assistant-input"
            type="textarea"
            maxlength="1000"
            :autosize="{ minRows: 3, maxRows: 7 }"
            placeholder="For example: every xAPI statement must contain an actor, verb, and object."
            :disabled="busy"
            aria-label="Describe your requirement"
            @keydown.enter.exact.prevent="send"
          />
          <div class="composer-footer">
            <span class="composer-hint"><kbd>Enter</kbd> to send <span class="composer-divider">·</span> <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line</span>
            <div class="assistant-actions">
              <n-button quaternary :disabled="busy || (!input.trim() && !messages.length)" @click="clear">Clear</n-button>
              <n-button class="send-button" type="primary" :loading="loading" :disabled="busy || !input.trim()" @click="send">
                <template #icon><n-icon><ArrowUpIcon /></n-icon></template>
                Generate draft
              </n-button>
            </div>
          </div>
        </div>

        <section v-if="proposal" class="proposal-card" aria-label="Generated draft proposal">
          <div class="proposal-heading">
            <div class="proposal-heading-main">
              <div class="proposal-icon"><SparkleIcon /></div>
              <div>
                <span class="section-kicker">Generated draft</span>
                <h3>Review before applying</h3>
              </div>
            </div>
            <span class="draft-badge">Not saved</span>
          </div>
          <p class="proposal-note">Check the wording, fields, and implementation before applying this draft to the editor.</p>

          <div class="proposal-details">
            <div class="proposal-field proposal-field-wide">
              <span class="field-label">Requirement name</span>
              <strong>{{ proposal.name || 'Untitled requirement' }}</strong>
            </div>
            <div class="proposal-field proposal-field-wide">
              <span class="field-label">Description</span>
              <p>{{ proposal.description || 'No description was generated.' }}</p>
            </div>
            <div class="proposal-field">
              <span class="field-label">Quality aspect</span>
              <span class="value-chip">{{ labelFor(proposal.targetAspect) }}</span>
            </div>
            <div class="proposal-field">
              <span class="field-label">Criterion</span>
              <span class="value-chip">{{ labelFor(proposal.criterionType) }}</span>
            </div>
          </div>

          <div v-if="proposal.evaluationMethod" class="implementation-section">
            <div class="implementation-heading">
              <div><span class="section-kicker">Evaluation</span><strong>Implementation details</strong></div>
              <span class="engine-chip">{{ labelFor(proposal.evaluationMethod.engine) }}</span>
            </div>
            <div v-if="proposal.evaluationMethod.variableSchema" class="implementation-block">
              <span class="code-label">Variable schema</span>
              <AssistantJson :value="proposal.evaluationMethod.variableSchema" />
            </div>
            <div v-if="proposal.evaluationMethod.implementationTemplate" class="implementation-block">
              <span class="code-label">Implementation template</span>
              <pre class="implementation-code"><code>{{ proposal.evaluationMethod.implementationTemplate }}</code></pre>
            </div>
          </div>

          <div v-if="exampleGroups.length" class="examples-section">
            <div class="examples-heading">
              <div><span class="section-kicker">Try the rule</span><strong>Representative examples</strong></div>
              <span class="examples-count">{{ exampleCount }} {{ exampleCount === 1 ? 'case' : 'cases' }}</span>
            </div>
            <div class="example-grid">
              <article v-for="group in exampleGroups" :key="group.key" class="example-card" :class="group.key">
                <div class="example-card-heading">
                  <span class="example-status"><CheckIcon v-if="group.key === 'passing'" /><CrossIcon v-else /> {{ group.label }}</span>
                  <span>{{ group.items.length }} {{ group.items.length === 1 ? 'example' : 'examples' }}</span>
                </div>
                <div v-for="(item, index) in group.items" :key="group.key + '-' + index" class="example-item">
                  <span class="example-index">{{ String(index + 1).padStart(2, '0') }}</span>
                  <AssistantJson :value="item" />
                </div>
              </article>
            </div>
          </div>

          <n-button class="apply-button" type="primary" block @click="apply">
            <template #icon><n-icon><CheckIcon /></n-icon></template>
            Apply draft to editor
          </n-button>
        </section>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup>
import { computed, defineComponent, h, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { NAlert, NButton, NDrawer, NDrawerContent, NIcon, NInput } from 'naive-ui'
import { askTemplateAssistant, assistantErrorMessage } from '../api/assistant.js'
import { assistantTextChunks, normaliseAssistantExamples } from '../api/assistantPresentation.js'
import AssistantJson from './AssistantJson.vue'

const props = defineProps({ template: { type: Object, default: null } })
const emit = defineEmits(['apply'])

const open = ref(false)
const input = ref('')
const loading = ref(false)
const error = ref('')
const messages = ref([])
const proposal = ref(null)
const examples = ref(null)
const conversationEl = ref(null)
const revealingMessageId = ref(null)
const busy = computed(() => loading.value || revealingMessageId.value !== null)
let nextMessageId = 0
let revealTimer = null
let resolveReveal = null

const exampleGroups = computed(() => {
  const normalised = normaliseAssistantExamples(examples.value)
  return [
    { key: 'passing', label: 'Passes', items: normalised.passing },
    { key: 'failing', label: 'Fails', items: normalised.failing }
  ].filter(group => group.items.length)
})
const exampleCount = computed(() => exampleGroups.value.reduce((total, group) => total + group.items.length, 0))

function clone (value) {
  return value == null ? null : JSON.parse(JSON.stringify(value))
}

function labelFor (value) {
  if (!value) return 'Not specified'
  return String(value).toLowerCase().split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

function scrollConversation () {
  nextTick(() => {
    if (conversationEl.value) conversationEl.value.scrollTop = conversationEl.value.scrollHeight
  })
}

watch(() => [messages.value.length, loading.value, revealingMessageId.value], scrollConversation)

function stopReveal () {
  if (revealTimer !== null) {
    clearTimeout(revealTimer)
    revealTimer = null
  }
  if (resolveReveal) {
    const resolve = resolveReveal
    resolveReveal = null
    resolve()
  }
  revealingMessageId.value = null
}

function revealAssistantMessage (message, content) {
  stopReveal()
  const chunks = assistantTextChunks(content)
  return new Promise(resolve => {
    resolveReveal = resolve
    let index = 0

    const revealNext = () => {
      if (index >= chunks.length) {
        revealTimer = null
        const finish = resolveReveal
        resolveReveal = null
        revealingMessageId.value = null
        finish?.()
        return
      }
      message.content += chunks[index]
      index += 1
      scrollConversation()
      revealTimer = setTimeout(revealNext, 28)
    }

    revealingMessageId.value = message.id
    revealNext()
  })
}

async function send () {
  const message = input.value.trim()
  if (!message || busy.value) return
  messages.value.push({ id: ++nextMessageId, role: 'user', content: message })
  input.value = ''
  loading.value = true
  error.value = ''
  try {
    const response = await askTemplateAssistant({
      message,
      conversation: messages.value.slice(0, -1),
      currentTemplate: clone(props.template)
    })
    loading.value = false
    messages.value.push({ id: ++nextMessageId, role: 'assistant', content: '' })
    const assistantMessage = messages.value[messages.value.length - 1]
    await revealAssistantMessage(assistantMessage, response.message)
    proposal.value = response.proposal || null
    examples.value = response.examples || null
  } catch (cause) {
    error.value = assistantErrorMessage(cause)
  } finally {
    loading.value = false
  }
}

function clear () {
  stopReveal()
  messages.value = []
  proposal.value = null
  examples.value = null
  error.value = ''
}

onBeforeUnmount(stopReveal)

function apply () {
  if (!proposal.value) return
  emit('apply', clone(proposal.value))
}

const SparkleIcon = defineComponent({
  setup () {
    return () => h('svg', { viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
      h('path', { d: 'M12 2.75L13.55 8.45L19.25 10L13.55 11.55L12 17.25L10.45 11.55L4.75 10L10.45 8.45L12 2.75Z', fill: 'currentColor' }),
      h('path', { d: 'M19 15.5L19.7 18.3L22.5 19L19.7 19.7L19 22.5L18.3 19.7L15.5 19L18.3 18.3L19 15.5Z', fill: 'currentColor', opacity: '.7' })
    ])
  }
})

const UserIcon = defineComponent({
  setup () {
    return () => h('svg', { viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
      h('circle', { cx: '12', cy: '8', r: '3.2', fill: 'currentColor' }),
      h('path', { d: 'M5.5 20C5.5 16.4 8.15 14 12 14C15.85 14 18.5 16.4 18.5 20', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round' })
    ])
  }
})

const ArrowUpIcon = defineComponent({
  setup () {
    return () => h('svg', { viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
      h('path', { d: 'M12 19V5M6.5 10.5L12 5M12 5L17.5 10.5', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
})

const CheckIcon = defineComponent({
  setup () {
    return () => h('svg', { viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
      h('path', { d: 'M5 12.5L9.5 17L19 7.5', stroke: 'currentColor', 'stroke-width': '2.2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
})

const CrossIcon = defineComponent({
  setup () {
    return () => h('svg', { viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
      h('path', { d: 'M7 7L17 17M17 7L7 17', stroke: 'currentColor', 'stroke-width': '2.2', 'stroke-linecap': 'round' })
    ])
  }
})
</script>

<style scoped>
.assistant-launcher{display:inline-flex}.assistant-trigger{border-color:#0f766e;color:#0f766e;font-weight:700;transition:background .2s ease,border-color .2s ease}.assistant-trigger:hover{border-color:#115e59;background:#f0fdfa}.assistant-trigger :deep(.n-icon){color:#0f766e}.assistant-drawer :deep(.n-drawer-body-content){padding:0;background:#fff}.assistant-drawer-title{display:flex;align-items:center;gap:10px}.assistant-title-mark{display:grid;place-items:center;width:30px;height:30px;border:1px solid #0f766e;border-radius:8px;background:#f0fdfa;color:#0f766e}.assistant-title-mark svg{width:16px;height:16px}.assistant-kicker,.section-kicker{display:block;color:#0f766e;font-size:.59rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}.assistant-drawer-title strong{display:block;margin-top:2px;color:#0f172a;font-size:.91rem}.assistant-content{display:grid;gap:15px;padding:0 2px 20px}.assistant-intro{margin:0;padding:0 0 13px;border-bottom:1px solid #e2e8f0;color:#64748b;font-size:.73rem;line-height:1.5}.conversation{display:grid;gap:11px;max-height:390px;overflow-y:auto;padding:1px 2px 2px;scroll-behavior:smooth}.conversation-empty{display:grid;justify-items:center;padding:8px 12px 4px;text-align:center}.empty-icon{display:grid;place-items:center;width:36px;height:36px;margin-bottom:8px;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc;color:#64748b}.empty-icon svg{width:18px;height:18px}.conversation-empty strong{color:#334155;font-size:.78rem}.conversation-empty p{max-width:320px;margin:5px 0 0;color:#94a3b8;font-size:.7rem;line-height:1.45}.message{display:flex;align-items:flex-start;gap:8px;min-width:0}.message.user{flex-direction:row-reverse}.message-avatar{display:grid;flex:0 0 27px;place-items:center;width:27px;height:27px;border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc;color:#64748b}.message-avatar svg{width:15px;height:15px}.assistant .message-avatar{border-color:#a7f3d0;background:#ecfdf5;color:#0f766e}.message-content{min-width:0;max-width:88%}.message.user .message-content{text-align:right}.message-meta{display:flex;align-items:center;gap:5px;margin:0 2px 3px;color:#94a3b8;font-size:.58rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase}.message.user .message-meta{justify-content:flex-end}.ai-label{padding:2px 4px;border-radius:3px;background:#ecfdf5;color:#0f766e;font-size:.51rem}.message-content p{margin:0;padding:9px 11px;border:1px solid #e2e8f0;border-radius:4px 11px 11px 11px;background:#f8fafc;color:#475569;font-size:.73rem;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.message.user .message-content p{border-color:#bae6fd;border-radius:11px 4px 11px 11px;background:#f0f9ff;color:#164e63}.is-generating .message-content{flex:1}.generating-label{display:flex;align-items:center;gap:5px;color:#0f766e}.generating-dot,.typing-dot{width:6px;height:6px;border-radius:50%;background:#0f766e;box-shadow:0 0 0 3px #d1fae5}.generating-dot{animation:dot-pulse 1.2s ease-in-out infinite}.typing-card{display:flex;align-items:center;gap:8px;padding:10px 11px;border:1px solid #dbeafe;border-radius:4px 11px 11px 11px;background:#f8fafc;color:#475569;font-size:.71rem}.typing-dot{animation:dot-pulse 1.2s ease-in-out infinite}.typing-dots{display:inline-flex;gap:3px;margin-left:1px}.typing-dots i{width:3px;height:3px;border-radius:50%;background:#64748b;animation:dot-bounce 1.1s ease-in-out infinite}.typing-dots i:nth-child(2){animation-delay:.15s}.typing-dots i:nth-child(3){animation-delay:.3s}.assistant-error{margin:0}.assistant-error strong{display:block;margin-bottom:3px}.composer{padding:11px;border:1px solid #cbd5e1;border-radius:12px;background:#fff}.composer-label,.composer-footer{display:flex;align-items:center;justify-content:space-between;gap:10px}.composer-label{margin:0 2px 7px;color:#334155;font-size:.66rem;font-weight:800}.composer-label span:last-child{color:#94a3b8;font-weight:600}.assistant-input :deep(.n-input__textarea){font-size:.75rem;line-height:1.5}.assistant-input :deep(.n-input-wrapper){border-radius:8px}.composer-footer{margin-top:8px}.composer-hint{color:#94a3b8;font-size:.6rem}.composer-hint kbd{padding:2px 4px;border:1px solid #cbd5e1;border-bottom-width:2px;border-radius:3px;background:#f8fafc;color:#64748b;font:600 .57rem inherit}.composer-divider{padding:0 3px;color:#cbd5e1}.assistant-actions{display:flex;align-items:center;gap:5px}.send-button{font-size:.68rem;font-weight:700}.send-button :deep(.n-icon){width:13px;height:13px}.proposal-card{display:grid;gap:13px;padding:15px;border:1px solid #cbd5e1;border-radius:14px;background:#fff}.proposal-heading,.proposal-heading-main,.implementation-heading,.examples-heading{display:flex;align-items:center;justify-content:space-between;gap:10px}.proposal-heading-main{justify-content:flex-start}.proposal-icon{display:grid;flex:0 0 30px;place-items:center;width:30px;height:30px;border-radius:8px;background:#0f766e;color:#fff}.proposal-icon svg{width:16px;height:16px}.proposal-heading h3{margin:3px 0 0;color:#1e293b;font-size:.88rem}.draft-badge{padding:3px 6px;border:1px solid #cbd5e1;border-radius:999px;background:#f8fafc;color:#64748b;font-size:.55rem;font-weight:800;text-transform:uppercase}.proposal-note{margin:-2px 0 0;color:#64748b;font-size:.68rem;line-height:1.5}.proposal-details{display:grid;grid-template-columns:1fr 1fr;gap:8px}.proposal-field{display:grid;gap:4px;min-width:0;padding:9px 10px;border:1px solid #e2e8f0;border-radius:9px;background:#fff}.proposal-field-wide{grid-column:1/-1}.field-label,.code-label{color:#94a3b8;font-size:.56rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.proposal-field strong{color:#1e293b;font-size:.74rem;line-height:1.35;overflow-wrap:anywhere}.proposal-field p{margin:0;color:#475569;font-size:.69rem;line-height:1.45}.value-chip,.engine-chip{display:inline-flex;align-items:center;justify-self:start;padding:3px 6px;border-radius:5px;background:#f0fdfa;color:#0f766e;font-size:.63rem;font-weight:800}.implementation-section,.examples-section{display:grid;gap:9px;padding-top:2px}.implementation-heading>div,.examples-heading>div{display:grid;gap:3px}.implementation-heading strong,.examples-heading strong{color:#334155;font-size:.73rem}.engine-chip{border:1px solid #a7f3d0}.implementation-block{display:grid;gap:5px}.implementation-code{max-height:170px;overflow:auto;margin:0;padding:11px 12px;border:1px solid #1e293b;border-radius:9px;background:#0f172a;color:#bae6fd;font:500 .68rem/1.6 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,\"Liberation Mono\",\"Courier New\",monospace;white-space:pre-wrap;overflow-wrap:anywhere}.examples-heading{padding-top:3px}.examples-count{color:#94a3b8;font-size:.6rem;font-weight:700}.example-grid{display:grid;gap:8px}.example-card{display:grid;gap:8px;padding:10px;border:1px solid #bbf7d0;border-radius:10px;background:#f0fdf4}.example-card.failing{border-color:#fecaca;background:#fef2f2}.example-card-heading{display:flex;align-items:center;justify-content:space-between;color:#64748b;font-size:.59rem;font-weight:700}.example-status{display:flex;align-items:center;gap:4px;color:#15803d;font-size:.66rem;font-weight:800}.failing .example-status{color:#b91c1c}.example-status svg{width:13px;height:13px}.example-item{display:grid;grid-template-columns:22px minmax(0,1fr);gap:6px;align-items:start}.example-index{display:grid;place-items:center;width:22px;height:22px;border-radius:6px;background:#fff;color:#64748b;font:800 .56rem ui-monospace,monospace}.example-item :deep(.json-view){max-height:135px;padding:9px 10px;border-color:#334155;font-size:.63rem}.apply-button{height:38px;font-size:.7rem;font-weight:800}.apply-button :deep(.n-icon){width:14px;height:14px}@keyframes dot-pulse{0%,100%{transform:scale(.8);opacity:.55}50%{transform:scale(1.15);opacity:1}}@keyframes dot-bounce{0%,60%,100%{transform:translateY(0);opacity:.45}30%{transform:translateY(-3px);opacity:1}}@media(max-width:520px){.composer-footer{align-items:flex-end;flex-direction:column}.composer-hint{align-self:flex-start}.assistant-actions{width:100%;justify-content:flex-end}.proposal-details{grid-template-columns:1fr}.proposal-field-wide{grid-column:auto}}@media(prefers-reduced-motion:reduce){.assistant-trigger,.generating-dot,.typing-dot,.typing-dots i{animation:none;transition:none}}
.message.is-revealing .message-content p{border-color:#99f6e4}.typing-cursor{display:inline-block;width:2px;height:1em;margin-left:3px;vertical-align:-.15em;background:#0f766e;animation:cursor-blink .9s steps(1,end) infinite}.skeleton-card{display:grid;gap:9px;padding:11px;border:1px solid #dbe4ec;border-radius:4px 11px 11px 11px;background:#f8fafc}.skeleton-heading,.skeleton-row{display:grid;grid-template-columns:28px minmax(0,1fr);align-items:center;gap:8px}.skeleton-row{grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:10px}.skeleton-avatar,.skeleton-line{display:block;height:9px;border-radius:4px;background:#dce5ec;animation:skeleton-pulse 1.35s ease-in-out infinite}.skeleton-avatar{width:28px;height:28px;border-radius:8px}.skeleton-title{width:42%}.skeleton-wide{width:88%}.skeleton-medium{width:65%}.skeleton-short{width:54%}@keyframes skeleton-pulse{0%,100%{opacity:.45}50%{opacity:.95}}@keyframes cursor-blink{0%,45%{opacity:1}46%,100%{opacity:0}}@media(prefers-reduced-motion:reduce){.typing-cursor,.skeleton-avatar,.skeleton-line{animation:none}}
</style>
