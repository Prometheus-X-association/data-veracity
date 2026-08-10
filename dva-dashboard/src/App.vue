<template>
  <Header />

  <div class="content-wrapper">
    <sidebar-menu
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
  import Header from './components/Header.vue'
</script>

<script>
export default {
  name: 'App',
  data () {
    return {
      menu: [
        { header: 'Navigation' },
        {
          href: '/requests',
          title: 'Attestations',
          icon: {
            element: 'v-icon',
            attributes: { name: 'fa-list-ul' }
          }
        },
        {
          href: '/verifications',
          title: 'Verifications',
          icon: {
            element: 'v-icon',
            attributes: { name: 'fa-check-double' }
          }
        },
        {
          href: '/credentials',
          title: 'Credentials',
          icon: {
            element: 'v-icon',
            attributes: { name: 'fa-certificate' }
          }
        }
      ]
    }
  }
}
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
</style>
