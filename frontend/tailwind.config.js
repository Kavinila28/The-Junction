/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        junction: {
          bg: "#0a0f1e",
          panel: "#111a2e",
          panel2: "#16213b",
          line: "#1f2c47",
          accent: "#38bdf8",
          accent2: "#818cf8",
          success: "#34d399",
          warning: "#fbbf24",
          danger: "#f87171",
          critical: "#ef4444",
          muted: "#8da2c0",
        },
      },
      fontFamily: {
        display: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};