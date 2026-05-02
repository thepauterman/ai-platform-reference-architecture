import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/health': 'http://localhost:8080',
      '/query': 'http://localhost:8080',
      '/audit': 'http://localhost:8080',
      '/metrics': 'http://localhost:8080',
    },
  },
})
