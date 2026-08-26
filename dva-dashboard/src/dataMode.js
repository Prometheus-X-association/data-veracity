import { ref, watch } from 'vue'

const savedMode = typeof window !== 'undefined' ? window.localStorage.getItem('dva-data-mode') : null
export const demoMode = ref(savedMode === 'demo')

watch(demoMode, value => {
  if (typeof window !== 'undefined') window.localStorage.setItem('dva-data-mode', value ? 'demo' : 'live')
})
