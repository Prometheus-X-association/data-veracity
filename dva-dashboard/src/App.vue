<template>
  <Header @toggle-navigation="toggleNavigation" />

  <div class="content-wrapper">
    <button
      v-if="navigation.isOpen"
      class="navigation-backdrop"
      type="button"
      aria-label="Close navigation"
      @click="closeNavigation"
    ></button>

    <sidebar-menu
      class="dashboard-sidebar"
      :class="{ 'is-open': navigation.isOpen }"
      :menu="menu"
      width="220px"
      :relative="true"
      theme="white-theme"
    />

    <main class="content page-container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
  import { onBeforeUnmount, onMounted, reactive } from 'vue'
  import { useRouter } from 'vue-router'
  import Header from './components/Header.vue'
  import { createMobileNavigationState } from './utils/mobileNavigation.mjs'

  const router = useRouter()
  const navigation = reactive(createMobileNavigationState())
  const mobileMediaQuery = window.matchMedia('(max-width: 759px)')

  const menu = [
    { header: 'Navigation' },
    {
      href: '/overview',
      title: 'Overview',
      icon: { element: 'v-icon', attributes: { name: 'fa-chart-line' } }
    },
    {
      href: '/requests',
      title: 'Attestations',
      icon: { element: 'v-icon', attributes: { name: 'fa-list-ul' } }
    },
    {
      href: '/verifications',
      title: 'Verifications',
      icon: { element: 'v-icon', attributes: { name: 'fa-check-double' } }
    },
    {
      href: '/credentials',
      title: 'Credentials',
      icon: { element: 'v-icon', attributes: { name: 'fa-certificate' } }
    },
    { header: 'Environment' },
    {
      href: '/api-status',
      title: 'Gateway status',
      icon: { element: 'v-icon', attributes: { name: 'fa-server' } }
    }
  ]

  function updateViewport () {
    navigation.setViewport(mobileMediaQuery.matches)
  }

  function toggleNavigation () {
    if (navigation.isOpen) navigation.close()
    else navigation.open()
  }

  function closeNavigation () {
    navigation.close()
  }

  onMounted(() => {
    updateViewport()
    mobileMediaQuery.addEventListener('change', updateViewport)
    router.afterEach(() => navigation.routeChanged())
  })

  onBeforeUnmount(() => {
    mobileMediaQuery.removeEventListener('change', updateViewport)
  })
</script>

<style scoped>
  .content-wrapper {
    display: flex;
    min-height: calc(100vh - 82px);
    background: #f3f4f6;
  }

  .content {
    flex-grow: 1;
    min-width: 0;
  }

  .page-container {
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    padding: 24px;
    box-sizing: border-box;
  }

  .navigation-backdrop {
    display: none;
  }

  @media (max-width: 759px) {
    .content-wrapper {
      min-height: calc(100vh - 68px);
    }

    .dashboard-sidebar {
      position: fixed !important;
      z-index: 30;
      top: 68px;
      bottom: 0;
      left: 0;
      width: min(280px, calc(100vw - 48px)) !important;
      transform: translateX(-100%);
      transition: transform .2s ease;
      box-shadow: 10px 0 30px rgba(15, 23, 42, .12);
    }

    .dashboard-sidebar.is-open {
      transform: translateX(0);
    }

    .navigation-backdrop {
      position: fixed;
      z-index: 20;
      inset: 68px 0 0;
      display: block;
      width: 100%;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: rgba(15, 23, 42, .32);
    }

    .page-container {
      padding: 20px 16px 28px;
    }
  }
</style>
