import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import './style.css'
import ListView from './components/ListView.vue'
import CreateView from './components/CreateView.vue'
import FragmentsView from './components/FragmentsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/create' },
    { path: '/create', component: CreateView },
    { path: '/list', component: ListView }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
