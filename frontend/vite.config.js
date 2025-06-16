import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';



// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    hmr: false, // Отключаем горячую перезагрузку
    allowedHosts: [
      //'localhost', // Для локальной разработки
      //'5.159.101.115',
      'flashcardsapp.ru',
    ],
  },
});

