<template>
  <div class="content">
    <header>
      <h2>View VLAs</h2>
      <RouterLink to="/create"><button>Create new VLA</button></RouterLink>
    </header>
    <div class="main-part">
      <vue-json-pretty :data="vlas" :deep="1" />
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import VueJsonPretty from 'vue-json-pretty'
  import 'vue-json-pretty/lib/styles.css'

  const vlas = ref([])

  onMounted(async () => {
    const response = await axios.get('http://localhost:9091/vla')
    vlas.value = response.data
  })
</script>

<style scoped>
  h2 {
    justify-self: stretch;
    border-top: 4px solid #e08b1b;
    border-bottom: 4px solid #e08b1b;
    padding: 1rem;
    text-align: center;
    margin: 0;
    margin-bottom: 1rem;
  }

  .content {
    flex-grow: 1;
    flex-direction: column;
    display: flex;
    padding: 1rem;
    gap: 1rem;
  }

  .main-part {
    flex-grow: 1;
    display: flex;
  }
</style>
