/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary teal
        primary:   { DEFAULT: "#1a6b5e", light: "#d0f0eb", dark: "#0d3d35" },
        // Secondary brown
        secondary: { DEFAULT: "#7a5230", light: "#f5e8d8", dark: "#3d290f" },
        // States
        error:     { DEFAULT: "#b52235", light: "#fde8eb" },
        warning:   { DEFAULT: "#d97706", light: "#fef3c7" },
        success:   { DEFAULT: "#16a34a", light: "#dcfce7" },
        // Surface
        surface:   { DEFAULT: "#f9f9f9", variant: "#f0f0f0" },
      },
      borderRadius: {
        sm:  "8px",
        md:  "12px",
        lg:  "16px",
        xl:  "28px",
      },
      boxShadow: {
        card: "0 2px 8px 0 rgba(0,0,0,0.10)",
      },
      keyframes: {
        "alert-flash": {
          "0%,100%": { borderColor: "#b52235" },
          "50%":      { borderColor: "#f87171" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "alert-flash": "alert-flash 1.4s ease-in-out infinite",
        "fade-in":     "fade-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
};
