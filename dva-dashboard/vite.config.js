import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const DVA_API_URL = process.env.DVA_DASHBOARD_BACKEND_URL || 'http://localhost:9090'
const VLA_API_URL = process.env.DVA_DASHBOARD_VLA_API_URL || 'http://localhost:8000'
const VC_API_URL = process.env.DVA_DASHBOARD_VC_API_URL || 'http://localhost:8001'

const serviceProxy = (target, prefix) => ({
  target,
  changeOrigin: true,
  secure: false,
  rewrite: path => path.replace(prefix, '')
})

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api/dva': serviceProxy(DVA_API_URL, /^\/api\/dva/),
      '/api/vla': serviceProxy(VLA_API_URL, /^\/api\/vla/),
      '/api/vc': serviceProxy(VC_API_URL, /^\/api\/vc/)
    }
  }
})
