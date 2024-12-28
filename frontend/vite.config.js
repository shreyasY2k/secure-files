// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    include: ['chart.js', 'react-chartjs-2'],
  },
  server: {
    host: '0.0.0.0',
    port: 443,
    https: {
      key: fs.readFileSync('/etc/certs/frontend.key'),
      cert: fs.readFileSync('/etc/certs/frontend.crt'),
    },
  },
  build: {
    commonjsOptions: {
      include: [/node_modules/],
    },
    rollupOptions: {
      external: ['chart.js'],
      output: {
        manualChunks: {
          'chart.js': ['chart.js'],
          'react-chartjs-2': ['react-chartjs-2'],
        },
      },
    },
  },
});