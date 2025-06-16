<template>
  <div class="dashboard-wrapper">
    <h2 class="page-title">DVA Dashboard</h2>

    <section class="section">
      <div class="card-container">
        <p class="placeholder" v-if="reqs.length === 0">No requests yet</p>
        <RequestCard :req="req" v-for="req in reqs" :key="req.requestID"/>
      </div>
    </section>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import RequestCard from './RequestCard.vue'
  
  const reqs = ref([])
  
  onMounted(async () => {
    try {
      let url = '/api/requests'
      if (import.meta.env.MODE === 'production') {
        const BACKEND_URL = import.meta.env.VITE_BACKEND_BASE_URL || 'http://localhost:3000'
	url = `${BACKEND_URL}${url}`
      }
      const reqsFromAPI = await axios.get(url)
      reqs.value = reqsFromAPI.data
    } catch (err) {
      console.error('Fetch error:', err)
    }
  })
</script>

<style scoped>
  .dashboard-wrapper {
    padding: 1rem 1.5rem;
  }
  
  .page-title {
    text-align: center;
    margin-bottom: 1.5rem;
    font-size: 3rem;
    font-weight: 500;
  }
  
  /* Force exactly 4 columns */
  .card-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .placeholder {
    font-style: italic;
  }
</style>
