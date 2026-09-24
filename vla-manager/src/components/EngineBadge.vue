<template>
  <span class="engine-badge" :class="{ detailed }" :title="info.summary">
    <span class="engine-label"><span class="engine-kicker">Quality engine</span>{{ info.label }}</span>
    <span v-if="detailed && info.summary" class="engine-summary">{{ info.summary }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { engineInfo } from '../api/templatePresentation.js'

// Names the quality engine a template runs on; `detailed` adds what the
// engine checks.
const props = defineProps({
  engine: { type: String, default: '' },
  detailed: { type: Boolean, default: false }
})

const info = computed(() => engineInfo(props.engine))
</script>

<style scoped>
.engine-badge{display:inline-grid;gap:3px;justify-items:start;max-width:100%}.engine-label{display:inline-flex;align-items:center;gap:6px;padding:3px 8px;border:1px solid #99f6e4;border-radius:6px;background:#f0fdfa;color:#0f766e;font-size:.68rem;font-weight:800}.engine-kicker{color:#0d9488;font-size:.52rem;letter-spacing:.08em;text-transform:uppercase}.engine-summary{color:#64748b;font-size:.66rem;line-height:1.4}
</style>
