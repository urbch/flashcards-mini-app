import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';



// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    hmr: false, // Отключаем горячую перезагрузку
    allowedHosts: [
      'dc4b-194-58-154-209.ngrok-free.app', //бэкенд
      'ee0e-194-58-154-209.ngrok-free.app', //фронт
      'localhost', // Для локальной разработки
    ],
  },
});

