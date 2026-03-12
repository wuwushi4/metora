import process from 'node:process'
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8002/api'
  const apiTarget = process.env.API_PROXY_TARGET
    || apiBaseUrl.replace(/\/api$/, '')
    || 'http://localhost:8002'

  return {
    plugins: [
      vue(),
      VitePWA({
        registerType: 'prompt',
        manifest: {
          name: 'Metora — AI Agent Platform',
          short_name: 'Metora',
          description: 'Turn AI Agents into Real Systems',
          theme_color: '#0ea5e9',
          background_color: '#ffffff',
          display: 'standalone',
          start_url: '/',
          icons: [
            {
              src: '/favicon.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any maskable',
            },
          ],
        },
        workbox: {
          navigateFallbackDenylist: [/^\/api/],
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        },
        devOptions: {
          enabled: false,
        },
      }),
    ],

    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },

    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },

    preview: {
      port: 4173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
