<template>
  <div class="assistant-launcher">
    <n-button class="assistant-trigger" secondary @click="open = true">
      <template #icon><n-icon><SparkleIcon /></n-icon></template>
      <span>Design with AI</span>
      <span class="trigger-stars" aria-hidden="true">✦</span>
    </n-button>
  </div>

  <n-drawer v-model:show="open" placement="right" width="min(92vw, 480px)" class="assistant-drawer">
    <n-drawer-content closable :native-scrollbar="false">
      <template #header>
        <div class="assistant-drawer-title">
          <div class="assistant-title-mark"><SparkleIcon /></div>
          <div>
            <span class="assistant-kicker">AI template designer</span>
            <strong>Build a requirement</strong>
          </div>
        </div>
      </template>

      <div class="assistant-content">
        <section class="assistant-hero">
          <div class="hero-glow" aria-hidden="true"></div>
          <div class="hero-icon"><SparkleIcon /></div>
          <div class="hero-copy">
            <div class="hero-eyebrow"><span class="ready-dot"></span> Ready to design</div>
            <h2>Turn an idea into a VLA check</h2>
            <p>Describe the data rule in your own words. You will review every field before it reaches the editor.</p>
          </div>
        </section>

        <section ref="conversationEl" class="conversation" aria-live="polite" aria-label="Assistant conversation">
          <div v-if="!messages.length && !loading" class="conversation-empty">
            <div class="empty-icon"><SparkleIcon /></div>
            <strong>What should this data guarantee?</strong>
            <p>Start with a field, a value range, a freshness rule, or a schema requirement.</p>
            <div class="suggestions">
              <button v-for="suggestion in suggestions" :key="suggestion" type="button" @click="useSuggestion(suggestion)">
                <SparkleIcon />
                {{ suggestion }}
              </button>
            </div>
          </div>

          <article v-for="(item, index) in messages" :key="item.role + '-' + index" class="message" :class="item.role">
            <div class="message-avatar" aria-hidden="true">
              <UserIcon v-if="item.role === 'user'" />
              <SparkleIcon v-else />
            </div>
            <div class="message-content">
              <div class="message-meta">
                <span>{{ item.role === 'user' ? 'You' : 'VLA assistant' }}</span>
                <span v-if="item.role === 'assistant'" class="ai-label">AI</span>
              </div>
              <p>{{ item.content }}</p>
            </div>
          </article>

          <article v-if="loading" class="message assistant is-generating">
            <div class="message-avatar assistant-avatar" aria-hidden="true"><SparkleIcon /></div>
            <div class="message-content">
              <div class="message-meta"><span>VLA assistant</span><span class="generating-label"><span class="generating-dot"></span> Generating</span></div>
              <div class="typing-card">
                <div class="typing-title"><span class="typing-shimmer"></span> Drafting your requirement</div>
                <div class="typing-lines" aria-hidden="true"><span></span><span></span><span></span></div>
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
            show-count
            :autosize="{ minRows: 3, maxRows: 7 }"
            placeholder="For example: require every xAPI statement to contain an actor, verb, and object."
            :disabled="loading"
            aria-label="Describe your requirement"
            @keydown.enter.exact.prevent="send"
          />
          <div class="composer-footer">
            <span class="composer-hint"><kbd>Enter</kbd> to send <span class="composer-divider">·</span> <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line</span>
            <div class="assistant-actions">
              <n-button quaternary :disabled="loading || (!input.trim() && !messages.length)" @click="clear">Clear</n-button>
              <n-button class="send-button" type="primary" :loading="loading" :disabled="!input.trim()" @click="send">
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
          <p class="proposal-note">The assistant prepared this draft from your description. Check the wording, fields, and implementation before applying it.</p>

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
import { computed, defineComponent, h, nextTick, ref, watch } from 'vue'
import { NAlert, NButton, NDrawer, NDrawerContent, NIcon, NInput } from 'naive-ui'
import { askTemplateAssistant, assistantErrorMessage } from '../api/assistant.js'
import { normaliseAssistantExamples } from '../api/assistantPresentation.js'
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

const suggestions = [
  'Require an xAPI actor, verb, and object',
  'Keep hourly readings fresh and within range',
  'Validate a customer event JSON schema'
]

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

function useSuggestion (suggestion) {
  input.value = suggestion
}

function scrollConversation () {
  nextTick(() => {
    if (conversationEl.value) conversationEl.value.scrollTop = conversationEl.value.scrollHeight
  })
}

watch(() => [messages.value.length, loading.value], scrollConversation)

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
      h('path', { d: 'M12 19V5M6.5 10.5L12 5L17.5 10.5', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
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
.assistant-launcher{display:inline-flex}.assistant-trigger{position:relative;overflow:hidden;border:1px solid rgba(8,145,178,.35);background:linear-gradient(135deg,rgba(236,254,255,.96),rgba(239,246,255,.96));color:#0e7490;font-weight:700;box-shadow:0 5px 18px rgba(8,145,178,.12);transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}.assistant-trigger:hover{border-color:#06b6d4;box-shadow:0 8px 24px rgba(8,145,178,.2);transform:translateY(-1px)}.assistant-trigger :deep(.n-icon){color:#0891b2}.trigger-stars{position:absolute;top:3px;right:7px;color:#22d3ee;font-size:10px;animation:star-twinkle 2.2s ease-in-out infinite}.assistant-drawer :deep(.n-drawer-body-content){padding:0}.assistant-drawer-title{display:flex;align-items:center;gap:10px}.assistant-title-mark{display:grid;place-items:center;width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,#06b6d4,#6366f1);color:white;box-shadow:0 5px 16px rgba(6,182,212,.25)}.assistant-title-mark svg{width:18px;height:18px}.assistant-kicker,.section-kicker{display:block;color:#0891b2;font-size:.62rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.assistant-drawer-title strong{display:block;margin-top:2px;color:#0f172a;font-size:.95rem}.assistant-content{display:grid;gap:18px;padding:4px 2px 20px}.assistant-hero{position:relative;display:flex;gap:14px;overflow:hidden;padding:18px;border:1px solid rgba(103,232,249,.38);border-radius:18px;background:linear-gradient(135deg,#ecfeff 0%,#eef2ff 55%,#f5f3ff 100%)}.hero-glow{position:absolute;right:-35px;top:-45px;width:150px;height:150px;border-radius:50%;background:radial-gradient(circle,rgba(99,102,241,.25),transparent 68%);filter:blur(2px)}.hero-icon{position:relative;z-index:1;display:grid;flex:0 0 42px;place-items:center;width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,#0891b2,#6366f1);color:#fff;box-shadow:0 8px 22px rgba(8,145,178,.25);animation:hero-float 3.5s ease-in-out infinite}.hero-icon svg{width:23px;height:23px}.hero-copy{position:relative;z-index:1;min-width:0}.hero-eyebrow{display:flex;align-items:center;gap:6px;color:#0e7490;font-size:.65rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.ready-dot,.generating-dot{width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 0 4px rgba(16,185,129,.14)}.hero-copy h2{margin:5px 0 5px;color:#0f172a;font-size:1.16rem;line-height:1.2}.hero-copy p{margin:0;max-width:370px;color:#475569;font-size:.76rem;line-height:1.5}.conversation{display:grid;gap:12px;max-height:365px;overflow-y:auto;padding:1px 2px 2px;scroll-behavior:smooth}.conversation-empty{display:grid;justify-items:center;padding:12px 12px 2px;text-align:center}.empty-icon{display:grid;place-items:center;width:44px;height:44px;margin-bottom:9px;border-radius:50%;background:linear-gradient(135deg,#cffafe,#e0e7ff);color:#4f46e5}.empty-icon svg{width:21px;height:21px}.conversation-empty strong{color:#1e293b;font-size:.82rem}.conversation-empty p{max-width:300px;margin:5px 0 13px;color:#64748b;font-size:.72rem;line-height:1.45}.suggestions{display:flex;flex-wrap:wrap;justify-content:center;gap:7px}.suggestions button{display:flex;align-items:center;gap:5px;padding:7px 9px;border:1px solid #dbeafe;border-radius:999px;background:#fff;color:#334155;font:600 .66rem/1.2 inherit;cursor:pointer;transition:border-color .2s ease,color .2s ease,background .2s ease}.suggestions button:hover{border-color:#67e8f9;background:#ecfeff;color:#0e7490}.suggestions svg{width:12px;height:12px;color:#06b6d4}.message{display:flex;align-items:flex-start;gap:9px;min-width:0}.message.user{flex-direction:row-reverse}.message-avatar{display:grid;flex:0 0 29px;place-items:center;width:29px;height:29px;border-radius:10px;background:#e2e8f0;color:#64748b}.message-avatar svg{width:16px;height:16px}.assistant .message-avatar{background:linear-gradient(135deg,#cffafe,#e0e7ff);color:#4f46e5}.message-content{min-width:0;max-width:86%}.message.user .message-content{text-align:right}.message-meta{display:flex;align-items:center;gap:6px;margin:0 2px 4px;color:#64748b;font-size:.62rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.message.user .message-meta{justify-content:flex-end}.ai-label{padding:2px 5px;border-radius:4px;background:#eef2ff;color:#6366f1;font-size:.54rem}.message-content p{margin:0;padding:10px 12px;border:1px solid #e2e8f0;border-radius:4px 13px 13px 13px;background:#f8fafc;color:#334155;font-size:.75rem;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.message.user .message-content p{border-color:#bae6fd;border-radius:13px 4px 13px 13px;background:linear-gradient(135deg,#ecfeff,#eff6ff);color:#164e63}.is-generating .message-content{flex:1}.generating-label{display:flex;align-items:center;gap:5px;color:#6366f1}.generating-dot{background:#6366f1;box-shadow:0 0 0 4px rgba(99,102,241,.13);animation:dot-pulse 1.2s ease-in-out infinite}.typing-card{position:relative;overflow:hidden;padding:12px 13px;border:1px solid #ddd6fe;border-radius:4px 13px 13px 13px;background:linear-gradient(135deg,#f5f3ff,#eff6ff)}.typing-card::after{position:absolute;inset:0;content:\"\";background:linear-gradient(100deg,transparent 20%,rgba(255,255,255,.7) 50%,transparent 80%);transform:translateX(-100%);animation:typing-shimmer 1.8s ease-in-out infinite}.typing-title{position:relative;z-index:1;display:flex;align-items:center;gap:7px;color:#4338ca;font-size:.72rem;font-weight:700}.typing-shimmer{width:8px;height:8px;border-radius:50%;background:#8b5cf6;box-shadow:0 0 0 4px rgba(139,92,246,.13)}.typing-lines{position:relative;z-index:1;display:grid;gap:6px;margin-top:9px}.typing-lines span{display:block;height:6px;border-radius:999px;background:linear-gradient(90deg,#ddd6fe,#bfdbfe);animation:line-pulse 1.3s ease-in-out infinite}.typing-lines span:nth-child(1){width:92%}.typing-lines span:nth-child(2){width:72%;animation-delay:.15s}.typing-lines span:nth-child(3){width:46%;animation-delay:.3s}.assistant-error{margin:0}.assistant-error strong{display:block;margin-bottom:3px}.composer{padding:12px;border:1px solid #dbeafe;border-radius:16px;background:#fff;box-shadow:0 7px 24px rgba(15,23,42,.06)}.composer-label,.composer-footer{display:flex;align-items:center;justify-content:space-between;gap:10px}.composer-label{margin:0 2px 7px;color:#334155;font-size:.68rem;font-weight:800}.composer-label span:last-child{color:#94a3b8;font-weight:600}.assistant-input :deep(.n-input__textarea){font-size:.76rem;line-height:1.5}.assistant-input :deep(.n-input-wrapper){border-radius:11px}.composer-footer{margin-top:8px}.composer-hint{color:#94a3b8;font-size:.62rem}.composer-hint kbd{padding:2px 4px;border:1px solid #cbd5e1;border-bottom-width:2px;border-radius:4px;background:#f8fafc;color:#64748b;font:600 .58rem inherit}.composer-divider{padding:0 3px;color:#cbd5e1}.assistant-actions{display:flex;align-items:center;gap:5px}.send-button{font-size:.7rem;font-weight:700}.send-button :deep(.n-icon){width:14px;height:14px}.proposal-card{display:grid;gap:15px;padding:17px;border:1px solid #c7d2fe;border-radius:18px;background:linear-gradient(180deg,#fff 0%,#f8fafc 100%);box-shadow:0 10px 28px rgba(79,70,229,.1)}.proposal-heading,.proposal-heading-main,.implementation-heading,.examples-heading{display:flex;align-items:center;justify-content:space-between;gap:10px}.proposal-heading-main{justify-content:flex-start}.proposal-icon{display:grid;flex:0 0 34px;place-items:center;width:34px;height:34px;border-radius:11px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff}.proposal-icon svg{width:18px;height:18px}.proposal-heading h3{margin:3px 0 0;color:#1e1b4b;font-size:.95rem}.draft-badge{padding:4px 7px;border:1px solid #fed7aa;border-radius:999px;background:#fff7ed;color:#c2410c;font-size:.58rem;font-weight:800;text-transform:uppercase}.proposal-note{margin:-3px 0 0;color:#64748b;font-size:.7rem;line-height:1.5}.proposal-details{display:grid;grid-template-columns:1fr 1fr;gap:10px}.proposal-field{display:grid;gap:5px;min-width:0;padding:10px 11px;border:1px solid #e2e8f0;border-radius:11px;background:#fff}.proposal-field-wide{grid-column:1/-1}.field-label,.code-label{color:#94a3b8;font-size:.59rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.proposal-field strong{color:#1e293b;font-size:.76rem;line-height:1.35;overflow-wrap:anywhere}.proposal-field p{margin:0;color:#475569;font-size:.71rem;line-height:1.45}.value-chip,.engine-chip{display:inline-flex;align-items:center;justify-self:start;padding:4px 7px;border-radius:6px;background:#eef2ff;color:#4338ca;font-size:.66rem;font-weight:800}.implementation-section,.examples-section{display:grid;gap:10px;padding-top:2px}.implementation-heading>div,.examples-heading>div{display:grid;gap:3px}.implementation-heading strong,.examples-heading strong{color:#1e293b;font-size:.76rem}.engine-chip{background:#ecfeff;color:#0e7490}.implementation-block{display:grid;gap:6px}.implementation-code{max-height:190px;overflow:auto;margin:0;padding:14px 16px;border:1px solid rgba(148,163,184,.18);border-radius:12px;background:#0b1220;color:#bae6fd;font:500 .7rem/1.65 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,\"Liberation Mono\",\"Courier New\",monospace;white-space:pre-wrap;overflow-wrap:anywhere}.examples-heading{padding-top:4px}.examples-count{color:#94a3b8;font-size:.63rem;font-weight:700}.example-grid{display:grid;gap:10px}.example-card{display:grid;gap:9px;padding:11px;border:1px solid #bbf7d0;border-radius:12px;background:#f0fdf4}.example-card.failing{border-color:#fecaca;background:#fff7f7}.example-card-heading{display:flex;align-items:center;justify-content:space-between;color:#64748b;font-size:.61rem;font-weight:700}.example-status{display:flex;align-items:center;gap:5px;color:#15803d;font-size:.68rem;font-weight:800}.failing .example-status{color:#b91c1c}.example-status svg{width:14px;height:14px}.example-item{display:grid;grid-template-columns:23px minmax(0,1fr);gap:7px;align-items:start}.example-index{display:grid;place-items:center;width:23px;height:23px;border-radius:7px;background:rgba(255,255,255,.75);color:#64748b;font:800 .58rem ui-monospace,monospace}.example-item :deep(.json-view){max-height:145px;padding:10px 11px;border-color:rgba(148,163,184,.15);font-size:.65rem}.apply-button{height:40px;font-size:.72rem;font-weight:800}.apply-button :deep(.n-icon){width:15px;height:15px}@keyframes star-twinkle{0%,100%{opacity:.35;transform:scale(.85) rotate(0deg)}50%{opacity:1;transform:scale(1.15) rotate(12deg)}}@keyframes hero-float{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-4px) rotate(3deg)}}@keyframes typing-shimmer{0%{transform:translateX(-100%)}60%,100%{transform:translateX(100%)}}@keyframes line-pulse{0%,100%{opacity:.45}50%{opacity:1}}@keyframes dot-pulse{0%,100%{transform:scale(.8);opacity:.55}50%{transform:scale(1.15);opacity:1}}@media(max-width:520px){.assistant-content{gap:14px}.assistant-hero{padding:14px}.hero-copy h2{font-size:1rem}.composer-footer{align-items:flex-end;flex-direction:column}.composer-hint{align-self:flex-start}.assistant-actions{width:100%;justify-content:flex-end}.proposal-details{grid-template-columns:1fr}.proposal-field-wide{grid-column:auto}}@media(prefers-reduced-motion:reduce){.assistant-trigger,.hero-icon,.trigger-stars,.typing-card::after,.typing-lines span,.generating-dot{animation:none;transition:none}}
</style>
