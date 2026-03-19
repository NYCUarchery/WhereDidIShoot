import { aliases, mdi } from 'vuetify/iconsets/mdi'
import { createVuetify } from 'vuetify'

export default defineNuxtPlugin((nuxtApp) => {
  const vuetify = createVuetify({
    ssr: true,
    icons: {
      aliases,
      defaultSet: 'mdi',
      sets: { mdi },
    },
    defaults: {
      VAppBar: {
        elevation: 0,
      },
      VBtn: {
        rounded: 'xl',
      },
      VCard: {
        elevation: 0,
        rounded: 'xl',
      },
      VDialog: {
        scrollable: true,
      },
      VSelect: {
        density: 'comfortable',
        variant: 'outlined',
      },
      VTextarea: {
        autoGrow: true,
        rows: 3,
        variant: 'outlined',
      },
      VTextField: {
        density: 'comfortable',
        variant: 'outlined',
      },
    },
    theme: {
      defaultTheme: 'fieldBook',
      themes: {
        fieldBook: {
          dark: false,
          colors: {
            primary: '#2563eb',
            secondary: '#1d4ed8',
            accent: '#7dd3fc',
            background: '#eaf2ff',
            surface: '#f8fbff',
            'surface-bright': '#ffffff',
            success: '#4f7a50',
            warning: '#b7791f',
            error: '#b42318',
            info: '#0f6cbd',
          },
        },
      },
    },
  })

  nuxtApp.vueApp.use(vuetify)
})
