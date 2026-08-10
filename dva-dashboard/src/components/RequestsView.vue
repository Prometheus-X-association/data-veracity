<template>
  <section>
    <div class="page-header">
      <div><h2>Attestations</h2><p>Requests evaluated by the veracity service</p></div>
      <span class="count-badge">{{ reqs.length }}</span>
    </div>
    <div class="card-container">
      <p class="placeholder" v-if="reqs.length === 0">No requests yet</p>
      <RequestCard :req="req" v-for="req in reqs" :key="req.requestID"/>
    </div>
  </section>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import RequestCard from './RequestCard.vue'
  
  const reqs = ref([])
  
  onMounted(async () => {
    try {
      const [reqsFromAPI, vlasFromAPI] = await Promise.all([
        axios.get('/api/info/requests'),
        axios.get('/api/vla')
      ])
      const vlasById = new Map(vlasFromAPI.data.map(vla => [String(vla.id).toLowerCase(), vla]))
      reqs.value = reqsFromAPI.data.map(req => ({
        ...req,
        vla: req.vlaID ? vlasById.get(String(req.vlaID).toLowerCase()) : undefined
      }))
    } catch (err) {
      console.error('Fetch error:', err)
    }
  })
</script>

<style scoped>
  .card-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }

  .page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
  h2 { margin: 0; color: #0f172a; font-size: 1.65rem; }
  .page-header p { margin: 4px 0 0; color: #64748b; }
  .count-badge { padding: 5px 11px; border-radius: 999px; background: #cffafe; color: #0e7490; font-weight: 700; }

  .placeholder {
    font-style: italic;
  }

  @media (max-width: 1670px) {
    .card-container {
      grid-template-columns: repeat(3, 1fr);
    }
  }

  @media (max-width: 1350px) {
    .card-container {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 980px) {
    .card-container {
      grid-template-columns: repeat(1, 1fr);
    }
  }
</style>
