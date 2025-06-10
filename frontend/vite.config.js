import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,          // Доступ к серверу вне контейнера
    port: 5173,          // Порт Vite (по умолчанию)
    strictPort: true,    // Запрещает автоматический выбор порта
    hmr: false,
    watch: {
      usePolling: true,  // Необходимо для Docker на Windows/Mac
    },
    // Дополнительные хосты (если нужно)
    allowedHosts: [
      'lotus-ongoing-assign-academy.trycloudflare.com',
      'crawford-drilling-someone-populations.trycloudflare.com',
      'localhost',
    ],
  },
});
