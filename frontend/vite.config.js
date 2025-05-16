import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      '9335-194-58-154-209.ngrok-free.app', // Обновлённый ngrok-хост
      'localhost', // Для локальной разработки
    ],
  },
});