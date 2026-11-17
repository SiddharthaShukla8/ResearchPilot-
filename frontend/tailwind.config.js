/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5ff',
          100: '#e0ebff',
          200: '#c7d9fe',
          300: '#a3c0fd',
          400: '#799cfb',
          500: '#4f73f7',
          600: '#3553eb',
          700: '#273ed4',
          800: '#2334ab',
          900: '#223087',
          950: '#151c52',
        },
      },
    },
  },
  plugins: [],
};
