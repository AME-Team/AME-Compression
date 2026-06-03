import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

function cspPlugin(): Plugin {
  return {
    name: 'vite-plugin-csp',
    transformIndexHtml(_, { server }) {
      const isDev = !!server

      const connectSrc = isDev
        ? "'self' http://127.0.0.1:5000 http://localhost:5000 ws://localhost:5173 http://localhost:5173"
        : "'self' http://127.0.0.1:5000 http://localhost:5000"

      const styleSrc = isDev ? "'self' 'unsafe-inline'" : "'self'"

      const cspContent = [
        "default-src 'self'",
        "script-src 'self'",
        `style-src ${styleSrc}`,
        `connect-src ${connectSrc}`,
        "img-src 'self' data:",
        "font-src 'self'",
      ].join('; ')

      return [
        {
          tag: 'meta',
          attrs: {
            'http-equiv': 'Content-Security-Policy',
            content: cspContent,
          },
          injectTo: 'head' as const,
        },
      ]
    },
  }
}

export default defineConfig({
  plugins: [tailwindcss(), react(), cspPlugin()],
})
