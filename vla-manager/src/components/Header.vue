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
</style>
