import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    allowedHosts: [
      '.ngrok-free.dev',
      '.ngrok.dev',
      '.ngrok.io',
      '.trycloudflare.com',  // 🔥 Cloudflare Tunnel 域名
      'localhost',
      '127.0.0.1',
      '.local'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      }
    }
  }
})
