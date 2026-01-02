
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  
  root: '.',
  build: {
    
    outDir: 'dist', 
    emptyOutDir: true,
  },
  
  base: '/',
  test: {
    globals: true,
    environment: 'jsdom', 
    include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    watch: false,
    testTimeout: 5000,
    hookTimeout: 5000,
  }, 
});