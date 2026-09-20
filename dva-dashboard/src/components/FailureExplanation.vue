<template>
  <section class="failure-panel" :class="tone" aria-live="polite">
    <div class="failure-heading">
      <div class="failure-icon"><v-icon :name="icon" /></div>
      <div class="failure-title">
        <span>{{ heading }}</span>
        <strong>{{ failure.title }}</strong>
      </div>
      <span class="failure-state">{{ stateLabel }}</span>
    </div>

    <p class="failure-summary">{{ failure.summary }}</p>

    <div class="failure-grid">
      <div class="failure-section">
        <span class="section-label">What happened</span>
        <p>{{ failure.evidence }}</p>
      </div>
      <div class="failure-section">
        <span class="section-label">What to do next</span>
        <p>{{ failure.nextAction }}</p>
      </div>
    </div>

    <div class="failure-footer">
      <span class="failure-code">{{ failure.code || 'NO_FAILURE' }}</span>
      <span>{{ failure.retryable ? 'Retry may help' : 'Retry after correcting the cause' }}</span>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  failure: { type: Object, required: true },
  heading: { type: String, default: 'Evaluation result' }
})

const tone = computed(() => props.failure.status || 'error')
const stateLabel = computed(() => ({
  passed: 'Passed',
  pending: 'Pending',
  failed: 'Failed',
  invalid: 'Needs correction',
  unavailable: 'Unavailable',
  error: 'Error'
}[tone.value] || 'Review'))
const icon = computed(() => ({
  passed: 'fa-check',
  pending: 'fa-clock',
  failed: 'fa-exclamation-triangle',
  invalid: 'fa-pen',
  unavailable: 'fa-plug',
  error: 'fa-exclamation-circle'
}[tone.value] || 'fa-info-circle'))
</script>

<style scoped>
.failure-panel{margin-top:14px;padding:13px;border:1px solid #fecaca;border-radius:10px;background:#fff7f7;color:#475569}
.failure-heading{display:flex;align-items:center;gap:9px}.failure-icon{display:grid;place-items:center;width:29px;height:29px;border-radius:8px;color:#b91c1c;background:#fee2e2;font-size:.72rem}.failure-title{display:grid;min-width:0;flex:1;gap:2px}.failure-title span,.section-label{color:#94a3b8;font-size:.62rem;font-weight:800;letter-spacing:.04em;text-transform:uppercase}.failure-title strong{color:#7f1d1d;font-size:.74rem}.failure-state{padding:4px 7px;border-radius:999px;color:#991b1b;background:#fee2e2;font-size:.62rem;font-weight:800;white-space:nowrap}.failure-summary{margin:10px 0 0;color:#475569;font-size:.7rem;line-height:1.45}.failure-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:10px}.failure-section{min-width:0;padding:9px;border:1px solid #fee2e2;border-radius:8px;background:#fff}.failure-section p{margin:4px 0 0;color:#64748b;font-size:.68rem;line-height:1.45;overflow-wrap:anywhere}.failure-footer{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:10px;padding-top:9px;border-top:1px solid #fee2e2;color:#991b1b;font-size:.64rem}.failure-code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.6rem;font-weight:700;overflow-wrap:anywhere}.failure-panel.pending{border-color:#fde68a;background:#fffbeb}.failure-panel.pending .failure-icon,.failure-panel.pending .failure-state{color:#92400e;background:#fef3c7}.failure-panel.pending .failure-title strong{color:#92400e}.failure-panel.pending .failure-section{border-color:#fde68a}.failure-panel.pending .failure-footer{border-color:#fde68a;color:#92400e}.failure-panel.unavailable,.failure-panel.error{border-color:#cbd5e1;background:#f8fafc}.failure-panel.unavailable .failure-icon,.failure-panel.error .failure-icon,.failure-panel.unavailable .failure-state,.failure-panel.error .failure-state{color:#475569;background:#e2e8f0}.failure-panel.unavailable .failure-title strong,.failure-panel.error .failure-title strong{color:#334155}.failure-panel.unavailable .failure-section,.failure-panel.error .failure-section{border-color:#e2e8f0}.failure-panel.unavailable .failure-footer,.failure-panel.error .failure-footer{border-color:#e2e8f0;color:#475569}.failure-panel.passed{border-color:#bbf7d0;background:#f0fdf4}.failure-panel.passed .failure-icon,.failure-panel.passed .failure-state{color:#166534;background:#dcfce7}.failure-panel.passed .failure-title strong{color:#166534}.failure-panel.passed .failure-section{border-color:#bbf7d0}.failure-panel.passed .failure-footer{border-color:#bbf7d0;color:#166534}
@media(max-width:560px){.failure-grid{grid-template-columns:1fr}.failure-heading{align-items:flex-start}.failure-state{margin-left:auto}.failure-footer{align-items:flex-start;flex-direction:column;gap:4px}}
</style>
