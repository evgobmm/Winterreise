import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/Winterreise/',
  define: {
    // Метка сборки — показывается в меню печати, чтобы отличать кэшированную
    // версию от свежей (кэш GitHub Pages живёт до 10 минут)
    __BUILD_TS__: JSON.stringify(
      new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC'
    )
  }
})
