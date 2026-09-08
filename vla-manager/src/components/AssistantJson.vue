<template>
  <pre class="json-view"><code><span v-for="(token, index) in tokens" :key="index" :class="`json-${token.type}`">{{ token.text }}</span></code></pre>
</template>

<script setup>
import { computed } from 'vue'
import { tokeniseAssistantJson } from '../api/assistantPresentation.js'

const props = defineProps({ value: { type: null, default: null } })
const tokens = computed(() => tokeniseAssistantJson(props.value))
</script>

<style scoped>
.json-view{margin:0;max-height:240px;overflow:auto;padding:14px 16px;border:1px solid rgba(148,163,184,.18);border-radius:12px;background:#0b1220;color:#e2e8f0;font:500 .72rem/1.65 ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;white-space:pre-wrap;overflow-wrap:anywhere;tab-size:2}.json-key{color:#7dd3fc}.json-string{color:#86efac}.json-number{color:#fbbf24}.json-boolean{color:#c4b5fd}.json-null{color:#fda4af}.json-punctuation{color:#94a3b8}.json-plain{color:#e2e8f0}
</style>
