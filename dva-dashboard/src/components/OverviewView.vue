<template>
  <section>
    <div class="hero-row">
      <div>
        <div class="eyebrow">OPERATIONS OVERVIEW</div>
        <h1>Veracity at a glance</h1>
        <p class="lede">Monitor attestations, trusted credentials, and verification exchanges across your data-sharing network.</p>
      </div>
      <div class="hero-actions"><span class="source-chip"><i></i>{{ demoMode ? 'Demo data' : 'Live gateway data' }}</span><span class="updated"><v-icon name="fa-sync-alt" /> {{ lastUpdatedLabel }}</span><button class="primary-button" @click="refresh"><v-icon name="fa-redo" /> Refresh data</button></div>
    </div>

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.label" class="metric-card" :class="metric.tone">
        <div class="metric-icon"><v-icon :name="metric.icon" /></div>
        <div class="metric-copy"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.detail }}</small></div>
      </div>
    </div>

    <div class="content-grid">
      <div class="panel health-panel">
        <div class="panel-heading"><div><h2>Gateway health</h2><p>Live integration surface</p></div><span class="status-badge"><i></i> Healthy</span></div>
        <div class="health-list">
          <div v-for="service in services" :key="service.name" class="health-row"><div class="service-icon"><v-icon :name="service.icon" /></div><div class="service-copy"><strong>{{ service.name }}</strong><span>{{ service.description }}</span></div><div class="service-latency">{{ service.latency }}</div><div class="health-check"><v-icon name="fa-check" /></div></div>
        </div>
        <router-link class="panel-link" to="/api-status">View gateway details <v-icon name="fa-arrow-right" /></router-link>
      </div>
      <div class="panel activity-panel">
        <div class="panel-heading"><div><h2>Recent activity</h2><p>Latest veracity events</p></div><router-link to="/requests">View all</router-link></div>
        <div class="activity-list"><div v-for="item in recentActivity" :key="item.id" class="activity-row"><div class="activity-dot" :class="item.state"><v-icon :name="item.state === 'pass' ? 'fa-check' : item.state === 'pending' ? 'fa-clock' : 'fa-exclamation'" /></div><div class="activity-copy"><strong>{{ item.title }}</strong><span>{{ item.exchange }} · {{ item.time }}</span></div><span class="mini-status" :class="item.state">{{ item.label }}</span></div></div>
      </div>
    </div>

    <div class="section-heading"><div><h2>Quality performance</h2><p>Evaluation outcomes from the current reporting window</p></div><span class="window-pill">Last 24 hours</span></div>
    <div class="performance-panel panel"><div class="donut-wrap"><div class="donut" :style="{ '--pass-rate': `${passRate}%` }"><div><strong>{{ passRate }}%</strong><span>pass rate</span></div></div></div><div class="bar-area"><div class="bar-caption"><span>Successful evaluations</span><strong>{{ passing }} / {{ evaluatedCount }}</strong></div><div class="progress-track"><div class="progress-fill" :style="{ width: `${passRate}%` }"></div></div><div class="bar-legend"><span><i class="legend-pass"></i>Passed {{ passing }}</span><span><i class="legend-fail"></i>Pending {{ pendingCount }}</span><span class="score-label">Failed <strong>{{ failedCount }}</strong></span></div></div></div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { demoRequests } from '../demoData'
import { demoMode } from '../dataMode'

import { demoVLAs } from '../demoData'

const requests = ref([])
const contracts = ref([])
const lastUpdated = ref(null)
async function loadRequests () {
  if (demoMode.value) {
    requests.value = demoRequests
    contracts.value = demoVLAs
    lastUpdated.value = new Date()
    return
  }
  try {
    const [response, vlaResponse] = await Promise.all([axios.get('/api/info/requests'), axios.get('/api/vla')])
    requests.value = Array.isArray(response.data) ? response.data : []
    contracts.value = Array.isArray(vlaResponse.data) ? vlaResponse.data : []
    lastUpdated.value = new Date()
  } catch { requests.value = []; contracts.value = []; lastUpdated.value = new Date() }
}
onMounted(loadRequests)
watch(demoMode, loadRequests)
const passing = computed(() => requests.value.filter(item => item.evaluationPassing).length)
const pendingCount = computed(() => requests.value.filter(item => !item.evaluationDate).length)
const failedCount = computed(() => requests.value.filter(item => item.evaluationDate && item.evaluationPassing !== true).length)
const evaluatedCount = computed(() => passing.value + failedCount.value)
const passRate = computed(() => evaluatedCount.value ? Math.round((passing.value / evaluatedCount.value) * 100) : 0)
const lastUpdatedLabel = computed(() => lastUpdated.value ? `Updated ${lastUpdated.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Loading live data')
const metrics = computed(() => [
  { label: 'Attestation requests', value: requests.value.length, detail: demoMode.value ? 'Seeded records' : 'From DVA API gateway', icon: 'fa-list-ul', tone: 'cyan' },
  { label: 'Verified outcomes', value: passing.value, detail: `${passRate.value}% passing evaluations`, icon: 'fa-check-double', tone: 'green' },
  { label: 'Pending evaluations', value: pendingCount.value, detail: 'Awaiting processing', icon: 'fa-clock', tone: 'amber' },
  { label: 'Active data contracts', value: contracts.value.length, detail: demoMode.value ? 'Seeded contracts' : 'From DVA API gateway', icon: 'fa-file-contract', tone: 'blue' }
])
const services = [
  { name: 'DVA API gateway', description: 'Routing and policy enforcement', latency: '42 ms', icon: 'fa-route' },
  { name: 'Evaluation processor', description: 'Schema, JQ and quality engines', latency: '118 ms', icon: 'fa-microchip' },
  { name: 'Credential registry', description: 'Verifiable credential storage', latency: '86 ms', icon: 'fa-certificate' },
  { name: 'Event stream', description: 'Attestation lifecycle events', latency: '31 ms', icon: 'fa-wave-square' }
]
const recentActivity = computed(() => requests.value.slice(0, 5).map(item => { const state = !item.evaluationDate ? 'pending' : item.evaluationPassing === true ? 'pass' : 'fail'; return { id: item.requestID, title: `${item.type === 'pov' ? 'Proof' : 'Attestation'} ${state === 'pending' ? 'received' : 'evaluated'}`, exchange: item.exchangeID, time: formatRelativeTime(item.evaluationDate || item.receivedDate), state, label: state === 'pass' ? 'Passed' : state === 'pending' ? 'Pending' : 'Failed' } }))
function formatRelativeTime (value) { if (!value) return 'Time unavailable'; const diff = Math.max(0, Date.now() - new Date(value).getTime()); const minutes = Math.floor(diff / 60000); if (minutes < 1) return 'Just now'; if (minutes < 60) return `${minutes} min ago`; const hours = Math.floor(minutes / 60); if (hours < 24) return `${hours} hr ago`; return `${Math.floor(hours / 24)} days ago` }
const refresh = () => window.location.reload()
</script>

<style scoped>
  .hero-row, .panel-heading, .section-heading, .bar-caption, .bar-legend { display: flex; align-items: center; justify-content: space-between; }
  .hero-row { margin-bottom: 26px; gap: 20px; }
  .eyebrow { color: #0891b2; font-size: .7rem; font-weight: 800; letter-spacing: .14em; }
  h1 { margin: 6px 0 8px; color: #0f172a; font-size: 2.15rem; letter-spacing: -.045em; }
  h2 { margin: 0; color: #172033; font-size: 1.05rem; letter-spacing: -.02em; }
  p { margin: 0; color: #64748b; }
  .lede { max-width: 620px; font-size: .95rem; }
  .hero-actions { display: flex; align-items: center; gap: 18px; white-space: nowrap; }
  .updated { color: #64748b; font-size: .75rem; } .updated svg { margin-right: 5px; color: #0891b2; }
  .primary-button { display: flex; align-items: center; gap: 8px; border: 0; border-radius: 9px; padding: 10px 14px; color: white; background: #0e7490; font-size: .8rem; font-weight: 700; }
  .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 22px; }
  .metric-card, .panel { border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; box-shadow: 0 4px 18px rgba(15,23,42,.04); }
  .metric-card { display: flex; align-items: center; gap: 13px; padding: 17px; border-top: 3px solid transparent; } .metric-card.cyan { border-top-color: #06b6d4; } .metric-card.green { border-top-color: #22c55e; } .metric-card.amber { border-top-color: #f59e0b; } .metric-card.blue { border-top-color: #3b82f6; }
  .metric-icon, .service-icon { display: grid; place-items: center; width: 38px; height: 38px; border-radius: 10px; color: #0891b2; background: #ecfeff; } .green .metric-icon { color: #16a34a; background: #f0fdf4; } .amber .metric-icon { color: #d97706; background: #fffbeb; } .blue .metric-icon { color: #2563eb; background: #eff6ff; }
  .metric-copy { display: grid; gap: 2px; } .metric-copy span { color: #64748b; font-size: .72rem; } .metric-copy strong { color: #0f172a; font-size: 1.45rem; line-height: 1.1; } .metric-copy small { color: #94a3b8; font-size: .65rem; }
  .content-grid { display: grid; grid-template-columns: 1.1fr 1fr; gap: 18px; margin-bottom: 27px; } .panel { padding: 20px; } .panel-heading { margin-bottom: 15px; } .panel-heading p, .section-heading p { margin-top: 4px; font-size: .75rem; }
  .status-badge { display: flex; align-items: center; gap: 6px; padding: 5px 8px; border-radius: 999px; color: #15803d; background: #f0fdf4; font-size: .7rem; font-weight: 700; } .status-badge i { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; }
  .health-row, .activity-row { display: flex; align-items: center; gap: 11px; padding: 12px 0; border-top: 1px solid #f1f5f9; } .service-copy, .activity-copy { display: grid; flex: 1; gap: 2px; } .service-copy strong, .activity-copy strong { color: #334155; font-size: .78rem; } .service-copy span, .activity-copy span { color: #94a3b8; font-size: .68rem; } .service-latency { color: #64748b; font-size: .7rem; } .health-check { color: #16a34a; }
  .panel-link, .panel-heading a { display: inline-flex; align-items: center; gap: 7px; margin-top: 12px; color: #0891b2; font-size: .75rem; font-weight: 700; text-decoration: none; } .panel-heading a { margin: 0; }
  .activity-dot { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 9px; font-size: .68rem; } .activity-dot.success { color: #16a34a; background: #f0fdf4; } .activity-dot.warning { color: #d97706; background: #fffbeb; } .mini-status, .window-pill { padding: 5px 8px; border-radius: 999px; font-size: .64rem; font-weight: 700; } .mini-status.pass { color: #15803d; background: #f0fdf4; } .mini-status.fail { color: #991b1b; background: #fee2e2; } .mini-status.pending { color: #92400e; background: #fef3c7; }
  .section-heading { margin-bottom: 13px; } .window-pill { color: #64748b; background: #f8fafc; border: 1px solid #e2e8f0; }
  .performance-panel { display: flex; align-items: center; gap: 35px; } .donut-wrap { width: 140px; flex: 0 0 140px; } .donut { position: relative; display: grid; place-items: center; width: 130px; height: 130px; border-radius: 50%; background: conic-gradient(#06b6d4 var(--pass-rate), #e2e8f0 0); } .donut::after { content: ''; position: absolute; width: 96px; height: 96px; border-radius: 50%; background: white; } .donut > div { z-index: 1; display: grid; text-align: center; } .donut strong { font-size: 1.55rem; color: #0f172a; } .donut span { color: #94a3b8; font-size: .68rem; }
  .bar-area { flex: 1; } .bar-caption { color: #475569; font-size: .8rem; } .bar-caption strong { color: #0f172a; } .progress-track { height: 12px; margin: 13px 0 12px; overflow: hidden; border-radius: 99px; background: #f1f5f9; } .progress-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #06b6d4, #22c55e); } .bar-legend { justify-content: flex-start; gap: 18px; color: #64748b; font-size: .68rem; } .bar-legend i { display: inline-block; width: 7px; height: 7px; margin-right: 5px; border-radius: 50%; } .legend-pass { background: #06b6d4; } .legend-fail { background: #cbd5e1; } .score-label { margin-left: auto; } .score-label strong { color: #0f172a; }
  @media (max-width: 1050px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } .content-grid { grid-template-columns: 1fr; } } @media (max-width: 700px) { .hero-row, .performance-panel { align-items: flex-start; flex-direction: column; } .hero-actions { width: 100%; justify-content: space-between; } .metric-grid { grid-template-columns: 1fr; } .bar-legend { flex-wrap: wrap; } .score-label { margin-left: 0; } }
</style>
