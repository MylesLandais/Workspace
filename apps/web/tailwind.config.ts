import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "var(--theme-bg-primary)",
          surface: "var(--theme-bg-secondary)",
          "surface-hover": "var(--theme-bg-hover)",
          text: "var(--theme-text-primary)",
          muted: "var(--theme-text-secondary)",
          accent: "var(--theme-accent-primary)",
          "accent-hover": "var(--theme-accent-secondary)",
          "accent-light": "var(--theme-accent-tertiary)",
          border: "var(--theme-border-primary)",
        },
        // Matcha theme colors (emerald with cozy vibes)
        matcha: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
          950: "#052e16",
        },
        // Industrial theme colors (from grid-stuff)
        industrial: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          925: "#0a0f1a",
          950: "#020617",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["'Courier New'", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
