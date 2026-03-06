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
        target: 'http://127.0.0.1:8000',  // 로컬 FastAPI 서버
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',  // 변경: '../Board_Backend/...' → 'dist'
  },
});