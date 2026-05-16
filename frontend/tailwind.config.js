/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#f6f3ea',
        ink: '#101114',
        graphite: '#60616a',
        yolk: '#facc15',
        honey: '#f6d34b',
        mint: '#dff4e8',
        skysoft: '#dcecff',
        clay: '#e6d4c0'
      },
      boxShadow: {
        paper: '0 18px 45px rgba(16, 17, 20, 0.08)'
      }
    }
  },
  plugins: []
};
