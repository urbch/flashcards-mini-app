import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';



// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    hmr: false, // Отключаем горячую перезагрузку
    allowedHosts: [
      'dd3e-194-58-154-209.ngrok-free.app', //фронт
      '469a-194-58-154-209.ngrok-free.app', //бэкенд
      'localhost', // Для локальной разработки
    ],
  },
});

