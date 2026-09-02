<template>
  <article class="card">
    <div class="card-header">
      <div class="credential-mark"><v-icon name="fa-certificate" /></div>
      <div class="header-copy"><span>Verifiable credential</span><h3>{{ attrs.vc_id || 'Credential' }}</h3></div>
      <span class="status" :class="attrs.status === 'revoked' ? 'revoked' : 'verified'"><i></i>{{ attrs.status || 'verified' }}</span>
    </div>
    <div class="card-body">
      <div class="subject-row"><div class="subject-avatar"><v-icon name="fa-user" /></div><div><span class="label">Credential subject</span><strong>{{ attrs.subject || 'Not specified' }}</strong></div></div>
      <div class="field-grid">
        <div class="field"><span><v-icon name="fa-building" /> Issuer</span><strong>{{ attrs.issuer_id || '—' }}</strong></div>
        <div class="field"><span><v-icon name="fa-file-signature" /> Contract</span><strong>{{ attrs.contract_id || '—' }}</strong></div>
        <div class="field"><span><v-icon name="fa-exchange-alt" /> Exchange</span><strong>{{ attrs.data_exchange_id || '—' }}</strong></div>
        <div class="field"><span><v-icon name="fa-star" /> Quality score</span><strong>{{ attrs.quality_score || '—' }}</strong></div>
      </div>
      <div class="meta-row"><span><v-icon name="fa-calendar-alt" /> Issued {{ formatDate(attrs.issued_at) }}</span><span class="schema">{{ cred.schema_id || 'Schema unavailable' }}</span></div>
      <button class="json-button" @click="showJson = !showJson"><v-icon :name="showJson ? 'fa-chevron-up' : 'fa-code'" /> {{ showJson ? 'Hide JSON' : 'View JSON' }}</button>
      <div v-if="showJson" class="json-panel"><vue-json-pretty :data="cred" :deep="2" :virtual="true" :height="220" /></div>
    </div>
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'
const props = defineProps({ cred: { type: Object, required: true } })
const attrs = computed(() => props.cred?.attrs || {})
const showJson = ref(false)
function formatDate (value) { return value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'date unavailable' }
</script>

<style scoped>
.card-header{background:#0e7490 !important}
.card{display:flex;flex-direction:column;height:100%;overflow:hidden;border:1px solid #e2e8f0;border-radius:14px;background:#fff;box-shadow:0 4px 18px rgba(15,23,42,.045);transition:transform .16s,box-shadow .16s}.card:hover{transform:translateY(-2px);box-shadow:0 10px 26px rgba(15,23,42,.09)}.card-header{display:flex;align-items:center;gap:11px;padding:16px;border-bottom:1px solid rgba(255,255,255,.15);color:#fff;background:linear-gradient(115deg,#0e7490,#0891b2)}.credential-mark{display:grid;place-items:center;width:37px;height:37px;border-radius:10px;color:#cffafe;background:rgba(255,255,255,.15);font-size:.95rem}.header-copy{min-width:0;flex:1}.header-copy span{display:block;color:#cffafe;font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em}.header-copy h3{overflow:hidden;margin:4px 0 0;font-size:.82rem;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.status{display:inline-flex;align-items:center;gap:5px;padding:5px 7px;border-radius:999px;font-size:.62rem;font-weight:800;text-transform:capitalize}.status i{width:6px;height:6px;border-radius:50%}.status.verified{color:#166534;background:#dcfce7}.status.verified i{background:#22c55e}.status.revoked{color:#991b1b;background:#fee2e2}.status.revoked i{background:#ef4444}.card-body{display:flex;flex:1;flex-direction:column;padding:16px}.subject-row{display:flex;align-items:center;gap:10px;margin-bottom:16px}.subject-avatar{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;color:#0e7490;background:#ecfeff}.label,.field span{display:block;color:#94a3b8;font-size:.65rem}.subject-row strong{display:block;margin-top:3px;color:#1e293b;font-size:.82rem}.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.field{min-width:0;padding:10px;border:1px solid #f1f5f9;border-radius:9px;background:#f8fafc}.field span{display:flex;align-items:center;gap:5px}.field span svg{color:#0891b2}.field strong{display:block;overflow:hidden;margin-top:5px;color:#475569;font-size:.7rem;text-overflow:ellipsis;white-space:nowrap}.meta-row{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-top:15px;padding-top:12px;border-top:1px solid #f1f5f9;color:#64748b;font-size:.65rem}.meta-row>span:first-child{display:flex;align-items:center;gap:5px;white-space:nowrap}.meta-row svg{color:#0891b2}.schema{overflow:hidden;color:#94a3b8;text-align:right;text-overflow:ellipsis;white-space:nowrap}.json-button{display:flex;align-items:center;justify-content:center;gap:7px;width:100%;margin-top:14px;padding:8px;border:1px solid #bae6fd;border-radius:8px;color:#0e7490;background:#f0f9ff;font-size:.7rem;font-weight:800;cursor:pointer}.json-button:hover{background:#e0f2fe}.json-panel{overflow:hidden;margin-top:10px;padding:9px;border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc}.json-panel :deep(.vjs-tree){font-size:.68rem}@media(max-width:420px){.field-grid{grid-template-columns:1fr}.meta-row{flex-direction:column}.schema{text-align:left}}
.status.verified{color:#166534;border:0;background:#dcfce7}.status.verified i{background:#22c55e}.status.revoked{color:#991b1b;border:0;background:#fee2e2}.status.revoked i{background:#ef4444}
@media(max-width:760px){.card:hover{transform:none}.card-header{padding:14px}.card-body{padding:14px}.field strong,.credential-line strong{white-space:normal;overflow-wrap:anywhere}.meta-row{flex-wrap:wrap}}
</style>
