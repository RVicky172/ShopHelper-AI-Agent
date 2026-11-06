import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'
import { learnPlugin } from './learn-plugin'

export default defineConfig({
  plugins: [react(), tailwindcss(), learnPlugin()],
  server: {
    port: 5173,
    watch: { usePolling: true }, // file events don't cross a Windows bind mount into Docker
    fs: { allow: ['..'] }, // lessons live in ../docs
    proxy: {
      // The browser calls /api/chat/stream; Vite forwards it to FastAPI as /chat/stream.
      '/api': {
        target: process.env.API_PROXY_TARGET ?? 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: { environment: 'node' },
})
