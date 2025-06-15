import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    hmr: false,
  },
  allowedHosts: [
    'dc4b-194-58-154-209.ngrok-free.app', //бэкенд
    'ee0e-194-58-154-209.ngrok-free.app', //фронт
    'localhost', // Для локальной разработки
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    css: true,
    testTimeout: 10000,
    environmentOptions: {
      jsdom: {
        pretendToBeVisual: true,
      },
    },
    server: {
      deps: {
        inline: ['@twa-dev/sdk'],
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});

