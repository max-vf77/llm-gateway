import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 12001,
    cors: true,
    allowedHosts: ['all', 'work-2-somxsohfynkrloox.prod-runtime.all-hands.dev'],
    headers: {
      'X-Frame-Options': 'ALLOWALL',
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 12001,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
