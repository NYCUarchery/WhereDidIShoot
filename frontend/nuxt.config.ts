const hmrClientPort = process.env.NUXT_HMR_CLIENT_PORT
const usePolling = process.env.CHOKIDAR_USEPOLLING === 'true'

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: true,
  devtools: { enabled: false },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    apiInternalBase: process.env.NUXT_API_INTERNAL_BASE || 'http://backend:5000/api',
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
    },
  },
  nitro: {
    compressPublicAssets: true,
  },
  vite: {
    server: {
      hmr: hmrClientPort
        ? {
            clientPort: Number(hmrClientPort),
            protocol: 'ws',
          }
        : undefined,
      watch: usePolling
        ? {
            interval: Number(process.env.CHOKIDAR_INTERVAL || '300'),
            usePolling: true,
          }
        : undefined,
    },
  },
  app: {
    head: {
      title: 'WhereDidIShoot',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'Nuxt 3 + Flask + MariaDB + Nginx starter stack.',
        },
      ],
    },
  },
})
