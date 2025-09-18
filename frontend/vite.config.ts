import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { readFileSync, existsSync } from 'fs'
import { resolve } from 'path'

// 嘗試讀取 HTTPS 憑證，如果失敗則使用 HTTP
function getHttpsConfig() {
  try {
    const keyPath = resolve(__dirname, 'certs/localhost-key.pem')
    const certPath = resolve(__dirname, 'certs/localhost.pem')
    
    if (existsSync(keyPath) && existsSync(certPath)) {
      return {
        key: readFileSync(keyPath),
        cert: readFileSync(certPath),
      }
    }
  } catch (error) {
    console.warn('HTTPS 憑證讀取失敗，使用 HTTP:', error instanceof Error ? error.message : String(error))
  }
  return undefined
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    host: true, // expose on LAN (0.0.0.0)
    ...(getHttpsConfig() && { https: getHttpsConfig() }),
    port: 5173,
  },
})
