import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const BACKEND_URL = process.env.DVA_DASHBOARD_BACKEND_URL || 'http://localhost:3000'
const VLA_MANAGER_URL = process.env.DVA_DASHBOARD_VLA_MANAGER_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api/vla': {
        target: VLA_MANAGER_URL,
        changeOrigin: true,
        secure: false,
        rewrite: path => path.replace(/^\/api/, '')
      },
      '/api/': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false
      }
    }
  }
})
