<template>
  <section>
    <div class="page-header">
      <div><div class="eyebrow">INTEGRATION MONITOR</div><h2>Service status</h2><p>HTTP services used by the dashboard.</p></div>
      <span class="status-badge" :class="overallTone"><i></i>{{ overallLabel }}</span>
    </div>
    <div class="mode-panel"><div><strong>Data source</strong><span>{{ demoMode ? 'Demo data' : 'Live data' }} · {{ demoMode ? 'Bundled records for UI review' : 'Checked against the DVA API gateway' }}</span></div><button class="mode-toggle" :class="{ demo: demoMode }" @click="demoMode = !demoMode"><span class="toggle-track"><i></i></span>{{ demoMode ? 'Demo data' : 'Live data' }}</button></div>
    <div class="status-grid"><div v-for="service in services" :key="service.name" class="status-card"><div class="status-icon"><v-icon :name="service.icon" /></div><div><strong>{{ service.name }}</strong><span>{{ service.endpoint }}</span></div><div class="status-bottom" :class="service.status"><span><i></i> {{ statusLabel(service.status) }}</span><b>{{ service.latency }}</b></div></div></div>
    <div class="note"><v-icon name="fa-info-circle" /><span><strong>{{ demoMode ? 'Demo data is active.' : 'Live checks are active.' }}</strong> {{ overallNote }}</span></div>
  </section>
</template>

<script setup>
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import { demoMode } from '../dataMode'
import { dashboardEndpoints } from '../api/endpoints.js'

const serviceDefinitions = [
  { name: 'DVA API', endpoint: '/info/requests', probe: dashboardEndpoints.requests, icon: 'fa-route' },
  { name: 'VLA Manager API', endpoint: '/vla', probe: dashboardEndpoints.vlas, icon: 'fa-file-contract' },
  { name: 'VC Manager credentials', endpoint: '/admin/credentials', probe: dashboardEndpoints.credentials, icon: 'fa-certificate' },
  { name: 'VC Manager verifications', endpoint: '/admin/verifications', probe: dashboardEndpoints.verifications, icon: 'fa-user-shield' }
]
const services = ref(serviceDefinitions.map(service => ({ ...service, status: 'checking', latency: 'Checking' })))
const overallTone = computed(() => services.value.some(service => service.status === 'unavailable') ? 'degraded' : services.value.some(service => service.status === 'checking') ? 'checking' : 'healthy')
const overallLabel = computed(() => ({ healthy: 'All checks passed', degraded: 'Action required', checking: 'Checking services' }[overallTone.value]))
const overallNote = computed(() => overallTone.value === 'healthy' ? 'All monitored endpoints responded successfully.' : overallTone.value === 'degraded' ? 'One or more endpoints did not respond. Open that service or try again after checking the gateway.' : 'The dashboard is checking the monitored endpoints.')

function statusLabel (status) { return ({ operational: 'Operational', unavailable: 'Unavailable', checking: 'Checking' }[status] || 'Unknown') }
async function checkServices () {
  if (demoMode.value) {
    services.value = serviceDefinitions.map(service => ({ ...service, status: 'operational', latency: 'Demo' }))
    return
  }
  services.value = serviceDefinitions.map(service => ({ ...service, status: 'checking', latency: 'Checking' }))
  const results = await Promise.all(serviceDefinitions.map(async service => {
    const started = performance.now()
    try {
      await axios.get(service.probe)
      return { ...service, status: 'operational', latency: `${Math.max(1, Math.round(performance.now() - started))} ms` }
    } catch {
      return { ...service, status: 'unavailable', latency: 'Unavailable' }
    }
  }))
  services.value = results
}

onMounted(checkServices)
watch(demoMode, checkServices)
</script>

<style scoped>
.page-header{display:flex;align-items:flex-end;justify-content:space-between;gap:15px;margin-bottom:24px}.eyebrow{color:#0891b2;font-size:.7rem;font-weight:800;letter-spacing:.14em}h2{margin:6px 0 5px;font-size:1.7rem;letter-spacing:-.04em}p{margin:0;color:#64748b;font-size:.85rem}.status-badge{display:flex;align-items:center;gap:6px;padding:7px 10px;border-radius:999px;color:#15803d;background:#f0fdf4;font-size:.72rem;font-weight:700}.status-badge i,.status-bottom i{width:7px;height:7px;display:inline-block;border-radius:50%;background:#22c55e}.status-badge.degraded{color:#991b1b;background:#fef2f2}.status-badge.degraded i{background:#ef4444}.status-badge.checking{color:#92400e;background:#fffbeb}.status-badge.checking i{background:#f59e0b}.mode-panel{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:18px;padding:15px 17px;border:1px solid #bae6fd;border-radius:12px;background:#f0f9ff}.mode-panel strong,.mode-panel span{display:block}.mode-panel strong{color:#0f172a;font-size:.82rem}.mode-panel div>span{margin-top:4px;color:#64748b;font-size:.72rem}.mode-toggle{display:flex;align-items:center;gap:9px;min-width:122px;justify-content:center;min-height:40px;padding:8px 12px;border:1px solid #bae6fd;border-radius:999px;color:#0369a1;background:#fff;font-size:.74rem;font-weight:800;cursor:pointer}.toggle-track{position:relative;width:30px;height:17px;border-radius:999px;background:#0e7490}.toggle-track i{position:absolute;top:3px;left:16px;width:11px;height:11px;border-radius:50%;background:#fff;transition:.2s}.mode-toggle.demo{color:#92400e;border-color:#fde68a;background:#fffbeb}.mode-toggle.demo .toggle-track{background:#f59e0b}.mode-toggle.demo .toggle-track i{left:3px}.status-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:15px}.status-card{display:grid;grid-template-columns:auto 1fr;gap:14px;padding:19px;border:1px solid #e2e8f0;border-radius:12px;background:#fff;box-shadow:0 4px 18px rgba(15,23,42,.04)}.status-icon{display:grid;place-items:center;width:42px;height:42px;color:#0891b2;border-radius:11px;background:#ecfeff}.status-card strong,.status-card span{display:block}.status-card strong{color:#334155;font-size:.86rem}.status-card>div:nth-child(2) span{margin-top:4px;color:#94a3b8;font-size:.7rem;overflow-wrap:anywhere}.status-bottom{grid-column:1/-1;display:flex;justify-content:space-between;gap:10px;padding-top:13px;border-top:1px solid #f1f5f9;color:#15803d;font-size:.7rem}.status-bottom b{color:#64748b;font-weight:600}.status-bottom.unavailable{color:#991b1b}.status-bottom.unavailable i{background:#ef4444}.status-bottom.checking{color:#92400e}.status-bottom.checking i{background:#f59e0b}.note{display:flex;gap:10px;margin-top:18px;padding:14px;border:1px solid #bae6fd;border-radius:10px;color:#0369a1;background:#f0f9ff;font-size:.75rem}.note svg{margin-top:2px}
@media(max-width:700px){.page-header{align-items:flex-start;flex-direction:column}.mode-panel{align-items:flex-start;flex-direction:column}.status-grid{grid-template-columns:1fr}.mode-toggle{width:100%}}@media(max-width:760px){.status-card{grid-template-columns:auto minmax(0,1fr);padding:16px}.status-bottom{flex-wrap:wrap}.note{align-items:flex-start}}
</style>
