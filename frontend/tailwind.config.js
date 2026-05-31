/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bjj: {
          purple: "#7C3AED",
          "purple-light": "#A78BFA",
          "purple-dark": "#5B21B6",
        },
        gi: "#1D4ED8",
        nogi: "#DC2626",
        belt: {
          white: "#F8FAFC",
          blue: "#1D4ED8",
          purple: "#7C3AED",
          brown: "#92400E",
          black: "#111827",
        },
      },
    },
  },
  plugins: [],
};
