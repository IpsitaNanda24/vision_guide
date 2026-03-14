import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/analyze_scene': 'http://localhost:8000',
      '/analyze_audio': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
      '/ws/live': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
