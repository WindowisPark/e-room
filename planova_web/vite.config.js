// vite.config.js 수정
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  base: "/",  // 변경: "/static/" → "/"
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://api.planova.kr',  // FastAPI 서버로 변경
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',  // 변경: '../Board_Backend/...' → 'dist'
  },
});