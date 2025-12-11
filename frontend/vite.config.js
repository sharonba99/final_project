// frontend/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Use the default Vite root (the frontend folder)
  root: '.',
  build: {
    // Output to the 'dist' folder
    outDir: 'dist', 
    emptyOutDir: true,
  },
  // Ensure base paths are correct for Nginx
  base: '/', 
});