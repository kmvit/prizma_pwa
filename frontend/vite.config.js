import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'images/prizma-logo-bubble.svg'],
      manifest: {
        name: 'PRIZMA - Психологический тест',
        short_name: 'PRIZMA',
        description: 'Психологический тест с ИИ-анализом',
        theme_color: '#1a1a2e',
        background_color: '#0f0f1a',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/images/prizma-logo-bubble.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        cleanupOutdatedCaches: true,
      },
      devOptions: { enabled: true },
    }),
  ],
  base: '/',
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
