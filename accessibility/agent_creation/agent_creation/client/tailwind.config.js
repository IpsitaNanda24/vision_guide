/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6C7CFF",
        secondary: "#A8B1FF",
        accent: "#FF6B6B",
        background: "#F5F7FF",
        card: "#FFFFFF",
        textMain: "#1A1A2E",
        borderLine: "#E4E7FF",
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
