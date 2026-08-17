<script setup>
import bmeLogo from '../assets/logo-bme.png'
import prometheusLogo from '../assets/logo-ptx.png'
</script>

<template>
  <header>
    <div class="brand-mark">DVA</div>
    <div>
      <h1>Data Veracity Assurance</h1>
      <p>Monitor attestations, verifications, and credentials</p>
    </div>
    <div class="partner-logos" aria-label="BME and Prometheus-X">
      <img :src="bmeLogo" alt="BME logo" />
      <span>×</span>
      <img :src="prometheusLogo" alt="Prometheus-X logo" />
    </div>
  </header>
</template>

<style scoped>
  header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 24px;
    min-height: 50px;
    background-color: #fff;
    border-bottom: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(15, 23, 42, .06);
  }

  .partner-logos {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
    padding-left: 22px;
    border-left: 1px solid #e2e8f0;
  }

  .partner-logos img {
    width: auto;
    height: 32px;
    max-width: 115px;
    object-fit: contain;
  }

  .partner-logos span {
    color: #94a3b8;
    font-size: 1.1rem;
  }

  .brand-mark {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: #0891b2;
    color: #fff;
    font-weight: 800;
  }

  header > div > h1 {
    color: #0f172a;
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
  }

  p {
    margin: 2px 0 0;
    color: #64748b;
    font-size: .85rem;
  }

  @media (max-width: 640px) {
    .partner-logos { padding-left: 10px; gap: 6px; }
    .partner-logos img { height: 24px; max-width: 78px; }
  }
</style>
