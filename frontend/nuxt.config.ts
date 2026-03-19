import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

const hmrClientPort = process.env.NUXT_HMR_CLIENT_PORT
const usePolling = process.env.CHOKIDAR_USEPOLLING === 'true'

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: true,
  devtools: { enabled: false },
  css: ['vuetify/styles', '@mdi/font/css/materialdesignicons.css', '~/assets/css/main.css'],
  build: {
    transpile: ['vuetify'],
  },
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
    ssr: {
      noExternal: ['vuetify'],
    },
    vue: {
      template: {
        transformAssetUrls,
      },
    },
    plugins: [vuetify({ autoImport: true })],
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
          content: 'Mobile-first archery practice logger for users, rounds, ends, and arrows.',
        },
      ],
    },
  },
})
