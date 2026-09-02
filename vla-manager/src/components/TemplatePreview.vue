<template>
  <n-card size="small" class="preview-card" title="Requirement preview">
    <div class="preview-meta">
      <n-tag size="small" type="info">{{ template.evaluationMethod?.engine || 'No engine' }}</n-tag>
      <n-text depth="3">{{ template.criterionType || 'No criterion' }} · {{ template.targetAspect || 'No quality aspect' }}</n-text>
    </div>
    <pre v-if="value" class="implementation">{{ value }}</pre>
    <n-empty v-else description="Render the template to see its implementation." size="small" />
  </n-card>
</template>

<script setup>
import { NCard, NEmpty, NTag, NText } from 'naive-ui'

defineProps({
  template: { type: Object, required: true },
  value: { type: String, default: '' }
})
</script>

<style scoped>
.preview-card{height:100%;border-radius:8px}.preview-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px;font-size:.72rem}.implementation{max-height:390px;margin:0;overflow:auto;padding:12px;border:1px solid #e2e8f0;border-radius:6px;color:#334155;background:#f8fafc;font: .72rem/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
</style>
