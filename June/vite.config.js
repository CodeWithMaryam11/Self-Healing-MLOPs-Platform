import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    watch: {
      // Exclude Python venv + MLflow artifacts from Vite's file watcher
      // This prevents the ENOSPC "too many file watchers" crash
      ignored: ['**/backend/venv/**', '**/backend/venv2/**', '**/backend/mlruns/**', '**/backend/mlflow.db', '**/node_modules/**'],
    },
  },
})
