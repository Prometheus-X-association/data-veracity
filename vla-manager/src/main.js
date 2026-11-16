import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

import App from './App.vue'
import './style.css'
import ListView from './components/ListView.vue'
import CreateView from './components/CreateView.vue'
import FragmentsView from './components/FragmentsView.vue'
import TemplatesView from './components/TemplatesView.vue'

if (import.meta.env.VITE_USE_MOCKS === 'true') {
  console.log('Using backend mock worker in dev mode')
  const { worker } = await import('./mocks/browser')
  await worker.start({ onUnhandledRequest: 'bypass' })
}

// Resolve API calls like '/api/...' relative to the app's base path
axios.defaults.baseURL = import.meta.env.BASE_URL

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/create' },
    { path: '/create', component: CreateView },
    { path: '/list', component: ListView },
    { path: '/templates', component: TemplatesView }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
