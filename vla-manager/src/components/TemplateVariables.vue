<template>
  <div class="template-variables">
    <n-table v-if="rows.length" size="small" :single-line="false" striped>
      <thead>
        <tr>
          <th>Variable</th>
          <th>Type</th>
          <th v-if="showValues">Value</th>
          <th v-else>Details</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.name">
          <td>
            <code class="name">{{ row.name }}</code>
            <span v-if="row.required" class="required">required</span>
          </td>
          <td>{{ row.type }}</td>
          <td v-if="showValues"><code class="value">{{ formatValue(values[row.name]) }}</code></td>
          <td v-else class="details">
            <span v-if="row.description">{{ row.description }}</span>
            <span v-if="row.constraints" class="constraints">{{ row.constraints }}</span>
            <span v-if="!row.description && !row.constraints" class="muted">–</span>
          </td>
        </tr>
      </tbody>
    </n-table>
    <p v-else class="muted">This template takes no variables.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { NTable } from 'naive-ui'
import { describeVariables } from '../api/templatePresentation.js'

// Lists a template's variables with their types; given `values`, it shows
// the value filled in for each variable instead of its details.
const props = defineProps({
  schema: { type: Object, default: null },
  values: { type: Object, default: null }
})

const rows = computed(() => describeVariables(props.schema))
const showValues = computed(() => props.values !== null)

function formatValue (value) {
  if (value === undefined) return 'not set'
  return typeof value === 'string' ? value : JSON.stringify(value)
}
</script>

<style scoped>
.template-variables{min-width:0;font-size:.7rem}.template-variables :deep(.n-table){font-size:.7rem}.template-variables :deep(th),.template-variables :deep(td){padding:6px 8px;vertical-align:top}.name,.value{font:600 .66rem/1.4 ui-monospace,monospace;overflow-wrap:anywhere}.value{font-weight:500;white-space:pre-wrap}.required{margin-left:6px;padding:1px 5px;border-radius:999px;background:#e0f2fe;color:#0369a1;font-size:.55rem;font-weight:800;text-transform:uppercase}.details{display:grid;gap:2px}.constraints{color:#64748b}.muted{margin:0;color:#94a3b8}
</style>
