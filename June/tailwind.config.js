/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Functional Colors Only per specifications
        healthy: {
          DEFAULT: '#10b981', // Green
          subtle: 'rgba(16, 185, 129, 0.1)',
        },
        warning: {
          DEFAULT: '#eab308', // Yellow
          subtle: 'rgba(234, 179, 8, 0.1)',
        },
        healing: {
          DEFAULT: '#3b82f6', // Blue
          subtle: 'rgba(59, 130, 246, 0.1)',
        },
        fault: {
          DEFAULT: '#ef4444', // Red
          subtle: 'rgba(239, 68, 68, 0.1)',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
