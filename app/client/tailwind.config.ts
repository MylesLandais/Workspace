import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
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
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
