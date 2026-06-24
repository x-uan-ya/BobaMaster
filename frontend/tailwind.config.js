/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      // ── Material Design 3 — Bobaflow Design Tokens ──────────────────
      colors: {
        // Primary — Teal
        primary: {
          DEFAULT: "hsl(174, 62%, 25%)",
          light:   "hsl(174, 62%, 90%)",
          dark:    "hsl(174, 62%, 15%)",
          on:      "hsl(0, 0%, 100%)",
        },
        // Secondary — Boba Brown
        secondary: {
          DEFAULT: "hsl(28, 35%, 35%)",
          light:   "hsl(28, 35%, 90%)",
          dark:    "hsl(28, 35%, 20%)",
          on:      "hsl(0, 0%, 100%)",
        },
        // Error / Alert — Crimson
        error: {
          DEFAULT: "hsl(354, 70%, 42%)",
          light:   "hsl(354, 70%, 92%)",
          on:      "hsl(0, 0%, 100%)",
        },
        // Warning — Amber
        warning: {
          DEFAULT: "hsl(38, 92%, 50%)",
          light:   "hsl(38, 92%, 92%)",
          on:      "hsl(0, 0%, 10%)",
        },
        // Success — Green
        success: {
          DEFAULT: "hsl(142, 71%, 35%)",
          light:   "hsl(142, 71%, 92%)",
          on:      "hsl(0, 0%, 100%)",
        },
        // Surface
        surface: {
          DEFAULT: "hsl(0, 0%, 98%)",
          variant: "hsl(0, 0%, 94%)",
          dark:    "hsl(0, 0%, 10%)",
        },
        // On-surface text
        "on-surface": {
          DEFAULT: "hsl(0, 0%, 10%)",
          muted:   "hsl(0, 0%, 45%)",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        "m3-xs": "4px",
        "m3-sm": "8px",
        "m3-md": "12px",
        "m3-lg": "16px",
        "m3-xl": "28px",
      },
      boxShadow: {
        "m3-1": "0 1px 2px 0 rgba(0,0,0,0.10)",
        "m3-2": "0 2px 6px 2px rgba(0,0,0,0.10)",
        "m3-3": "0 4px 8px 3px rgba(0,0,0,0.12)",
      },
      keyframes: {
        // Flashing outline for critical alert cards
        "alert-pulse": {
          "0%, 100%": { borderColor: "hsl(354, 70%, 42%)", opacity: "1" },
          "50%":       { borderColor: "hsl(354, 70%, 70%)", opacity: "0.7" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "alert-pulse": "alert-pulse 1.5s ease-in-out infinite",
        "fade-in":     "fade-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};
