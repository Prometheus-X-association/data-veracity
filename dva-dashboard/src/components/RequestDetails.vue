<template>
  <div class="request-details">
    <div class="section-title"><v-icon name="fa-database" /> Data</div>
    <vue-json-pretty :data="req.data" :deep="2" :virtual="true" :height="dataHeight" />
    <div class="section-title"><v-icon name="fa-chart-line" /> Evaluation results</div>
    <vue-json-pretty :data="evaluationResults" :deep="2" :virtual="true" :height="resultsHeight" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'

// The data and evaluation results of one attestation request, shared by the
// tile and the list view so both show the same thing.
const props = defineProps({
  req: { type: Object, required: true },
  dataHeight: { type: Number, default: 100 },
  resultsHeight: { type: Number, default: 150 }
})

// The API returns the results as an array; older records carry them as JSON text.
const evaluationResults = computed(() => {
  const value = props.req.evaluationResults
  if (value === null || value === undefined || value === '') return { status: 'Pending' }
  if (typeof value !== 'string') return value
  try { return JSON.parse(value) } catch { return { status: 'Unavailable' } }
})
</script>

<style scoped>
.section-title{display:flex;align-items:center;gap:6px;margin:14px 0 7px;padding-top:12px;border-top:1px solid #f1f5f9;color:#475569;font-size:.7rem;font-weight:800}
.section-title svg{color:#0891b2}
</style>
