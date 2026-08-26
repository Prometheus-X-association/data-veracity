<template>
  <div class="header-container">
    <div class="header-content">
      <div class="logo-wrapper">
        <img src="../assets/logo-bme.png" alt="BME Logo" class="logo" />
      </div>
      
      <div class="title-container">
        <n-h1 class="header-title">
          <span class="highlight">Veracity Level Agreement</span> Builder
        </n-h1>
        <nav class="header-nav" aria-label="Primary navigation">
          <router-link to="/create" active-class="is-active">Build</router-link>
          <router-link to="/list" active-class="is-active">Saved VLAs</router-link>
          <router-link to="/templates" active-class="is-active">Templates</router-link>
        </nav>
      </div>

      <div class="logo-wrapper ptx-logo">
        <img src="../assets/logo-ptx.png" alt="Prometheus-X Logo" class="logo" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { NH1 } from 'naive-ui'
</script>

<style scoped>
  .header-container {
    background: #ffffff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    border-bottom: 1px solid #e5e7eb;
  }
  
  .header-content {
    max-width: 1600px;
    margin: 0 auto;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .logo-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .logo {
    height: 50px;
    object-fit: contain;
  }
  
  .title-container {
    text-align: center;
    flex-grow: 1;
    min-width: 0;
  }

  .header-title {
    margin: 0 !important;
    color: #1f2937 !important;
    font-family: 'Inter', system-ui, sans-serif;
    font-weight: 600;
    font-size: 1.5rem;
    letter-spacing: -0.025em;
  }

  .highlight {
    color: #0891b2;
    font-weight: 700;
  }

  .header-nav {
    display: flex;
    justify-content: center;
    gap: 18px;
    margin-top: 6px;
  }

  .header-nav a {
    min-height: 32px;
    padding: 6px 4px;
    color: #64748b;
    font-size: .78rem;
    font-weight: 600;
    text-decoration: none;
  }

  .header-nav a:hover,
  .header-nav a.is-active {
    color: #0e7490;
  }

  .header-nav a:focus-visible {
    outline: 2px solid #67e8f9;
    outline-offset: 2px;
    border-radius: 4px;
  }

  @media (max-width: 700px) {
    .header-content { flex-wrap: wrap; gap: 10px; padding: 12px 16px; }
    .logo { height: 34px; max-width: 72px; }
    .title-container { order: 2; flex-basis: 100%; }
    .header-title { font-size: 1.1rem; line-height: 1.25; }
    .header-nav { gap: 12px; margin-top: 7px; }
    .header-nav a { min-height: 40px; padding: 9px 12px; border: 1px solid #dbe3ec; border-radius: 6px; background: #fff; }
  }
</style>
