<!-- src/App.vue -->
<template>
  <div class="container mt-4">
    <h2 class="mb-3">DVA Unified Dashboard</h2>
    <Dashboard />
  </div>
</template>

<script>
import Dashboard from './components/Dashboard.vue'

export default {
  components: { Dashboard }
}
</script>

<style>
/* (Optional) Global overrides */
</style>
