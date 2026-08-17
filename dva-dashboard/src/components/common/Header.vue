<script setup>
import bmeLogo from '../assets/logo-bme.png'
import prometheusLogo from '../assets/logo-ptx.png'
</script>

<template>
  <header class="topbar">
    <div class="brand-lockup">
      <div class="brand-mark"><v-icon name="fa-shield-alt" /></div>
      <div>
        <div class="brand-name">DVA Control Center</div>
        <div class="brand-subtitle">Data Veracity Assurance</div>
      </div>
    </div>
    <div class="topbar-meta">
      <span class="live-dot"></span>
      <span>Gateway connected</span>
      <span class="environment-pill">VERACITY NETWORK</span>
      <div class="partner-logos" aria-label="BME and Prometheus-X">
        <img :src="bmeLogo" alt="BME logo" />
        <span class="partner-cross">×</span>
        <img :src="prometheusLogo" alt="Prometheus-X logo" />
      </div>
    </div>
  </header>
</template>

<style scoped>
  .topbar { height: 82px; box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; padding: 0 30px; background: rgba(255,255,255,.95); border-bottom: 1px solid #e2e8f0; box-shadow: 0 2px 12px rgba(15,23,42,.04); z-index: 2; }
  .brand-lockup, .topbar-meta { display: flex; align-items: center; gap: 12px; }
  .brand-mark { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 12px; color: white; background: linear-gradient(135deg, #0891b2, #2563eb); box-shadow: 0 6px 14px rgba(8,145,178,.22); }
  .brand-name { color: #0f172a; font-weight: 800; letter-spacing: -.02em; }
  .brand-subtitle { color: #64748b; font-size: .75rem; margin-top: 1px; }
  .topbar-meta { color: #64748b; font-size: .8rem; }
  .live-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 4px #dcfce7; }
  .environment-pill { margin-left: 8px; padding: 6px 9px; color: #0e7490; border: 1px solid #a5f3fc; border-radius: 999px; background: #ecfeff; font-size: .65rem; font-weight: 800; letter-spacing: .08em; }
  .partner-logos { display: flex; align-items: center; gap: 9px; margin-left: 10px; padding-left: 14px; border-left: 1px solid #e2e8f0; }
  .partner-logos img { display: block; width: auto; height: 28px; max-width: 105px; object-fit: contain; }
  .partner-cross { color: #94a3b8; font-size: 1rem; font-weight: 500; }
  @media (max-width: 700px) { .topbar { padding: 0 16px; } .topbar-meta span:not(.live-dot), .partner-logos { display: none; } }
</style>
