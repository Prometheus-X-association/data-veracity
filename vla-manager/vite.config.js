import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const BACKEND_URL = process.env.VLA_MANAGER_BACKEND_URL || 'http://localhost:8000'

// Production builds use a placeholder base path which is replaced at container
// start-up with the value of the BASE_PATH env var (see misc/base-path.sh).
// This lets one image be served under any URL prefix, e.g. /worker/<name>/.
export const BASE_PATH_PLACEHOLDER = '/__DVA_BASE_PATH__/'

export default defineConfig(({ command }) => ({
  base: command === 'build' ? BASE_PATH_PLACEHOLDER : '/',
  plugins: [vue()],
  server: {
    proxy: {
      '/api/': {
        target: BACKEND_URL,
        changeOrigin: true,
        secure: false
      }
    }
  }
}))
