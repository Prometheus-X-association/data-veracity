<template>
  <n-alert :type="type" class="failure-explanation">
    <strong>{{ failure.title }}</strong>
    <p>{{ failure.summary }}</p>
    <div class="failure-detail"><span>Evidence</span>{{ failure.evidence }}</div>
    <div class="failure-detail"><span>Next step</span>{{ failure.nextAction }}</div>
    <div class="failure-footer"><code>{{ failure.code || 'NO_FAILURE' }}</code><span>{{ failure.retryable ? 'Retry may help' : 'Correct the cause before retrying' }}</span></div>
  </n-alert>
</template>

<script setup>
import { computed } from 'vue'
import { NAlert } from 'naive-ui'

const props = defineProps({ failure: { type: Object, required: true } })
const type = computed(() => props.failure.status === 'pending' ? 'warning' : props.failure.status === 'unavailable' || props.failure.status === 'error' ? 'default' : 'error')
</script>

<style scoped>
.failure-explanation{margin-top:14px}.failure-explanation p{margin:5px 0 10px;line-height:1.45}.failure-detail{display:grid;gap:3px;margin-top:8px;color:#475569;font-size:.78rem;line-height:1.45}.failure-detail span{color:#64748b;font-size:.68rem;font-weight:700;text-transform:uppercase}.failure-footer{display:flex;justify-content:space-between;gap:8px;margin-top:10px;padding-top:9px;border-top:1px solid rgba(100,116,139,.22);color:#64748b;font-size:.7rem}.failure-footer code{overflow-wrap:anywhere}
@media(max-width:520px){.failure-footer{align-items:flex-start;flex-direction:column}}
</style>
