<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-layout class="app-layout">
          <n-layout-header bordered>
            <Header />
          </n-layout-header>

          <n-layout-content class="app-content">
            <router-view />
          </n-layout-content>
        </n-layout>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
  import Header from './components/Header.vue'
  import {
    NConfigProvider,
    NMessageProvider,
    NDialogProvider,
    NLayout,
    NLayoutHeader,
    NLayoutContent
  } from 'naive-ui'

  const themeOverrides = {
    common: {
      primaryColor: '#0891b2',
      primaryColorHover: '#06b6d4',
      primaryColorPressed: '#0e7490',
      primaryColorSuppl: '#06b6d4',
      successColor: '#10b981',
      successColorHover: '#34d399',
      successColorPressed: '#059669',
      warningColor: '#f59e0b',
      errorColor: '#ef4444',
      infoColor: '#06b6d4',
      textColorBase: '#0f172a',
      textColor1: '#0f172a',
      textColor2: '#334155',
      textColor3: '#64748b',
      fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    },
    Card: {
      borderRadius: '8px',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
    }
  }
</script>

<style scoped>
  .app-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: transparent;
  }

  .app-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    background-color: #f3f4f6;
  }
</style>
