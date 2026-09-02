<template>
  <div class="filters">
    <n-input :value="query" clearable placeholder="Search templates" @update:value="$emit('update:query', $event)" />
    <n-select :value="engine" clearable placeholder="All engines" :options="engineOptions" @update:value="$emit('update:engine', $event)" />
    <n-select :value="aspect" clearable placeholder="All quality aspects" :options="aspectOptions" @update:value="$emit('update:aspect', $event)" />
    <n-button v-if="query || engine || aspect" quaternary @click="$emit('clear')">Clear filters</n-button>
  </div>
</template>

<script setup>
import { NButton, NInput, NSelect } from 'naive-ui'

defineProps({
  query: { type: String, default: '' },
  engine: { type: String, default: null },
  aspect: { type: String, default: null }
})
defineEmits(['update:query', 'update:engine', 'update:aspect', 'clear'])

const engineOptions = [
  { label: 'Schema', value: 'SCHEMA' },
  { label: 'JQ', value: 'JQ' },
  { label: 'Great Expectations', value: 'GREAT_EXPECTATIONS' }
]
const aspectOptions = [
  { label: 'Syntax', value: 'SYNTAX' },
  { label: 'Timeliness', value: 'TIMELINESS' },
  { label: 'Accuracy', value: 'ACCURACY' },
  { label: 'Completeness', value: 'COMPLETENESS' },
  { label: 'Consistency', value: 'CONSISTENCY' }
]
</script>

<style scoped>
.filters{display:grid;grid-template-columns:minmax(0,1fr) minmax(150px,180px) minmax(160px,200px) auto;gap:10px;align-items:center;padding:12px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;min-width:0}.filters :deep(.n-input),.filters :deep(.n-select){min-width:0}
@media(max-width:900px){.filters{grid-template-columns:minmax(0,1fr) minmax(150px,180px)}.filters :deep(.n-input){grid-column:1/-1}.filters :deep(.n-button){min-height:40px}}
@media(max-width:760px){.filters{grid-template-columns:1fr 1fr}.filters :deep(.n-button){min-height:40px}}
@media(max-width:430px){.filters{grid-template-columns:1fr}.filters :deep(.n-input){grid-column:auto}}
</style>
