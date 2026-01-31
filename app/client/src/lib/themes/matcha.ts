/**
 * Matcha Green Tea Theme
 *
 * Cozy emerald-based theme merging Bunny's existing design with dashboard aesthetics
 */

export const matchaTheme = {
  light: {
    primary: "#22c55e", // matcha-500
    primaryHover: "#16a34a", // matcha-600
    secondary: "#86efac", // matcha-300
    background: "#f0fdf4", // matcha-50
    surface: "#ffffff",
    surfaceHover: "#dcfce7", // matcha-100
    text: "#14532d", // matcha-900
    textMuted: "#166534", // matcha-800
    border: "#bbf7d0", // matcha-200
    accent: "#4ade80", // matcha-400
  },
  dark: {
    primary: "#22c55e", // matcha-500
    primaryHover: "#4ade80", // matcha-400
    secondary: "#15803d", // matcha-700
    background: "#020617", // industrial-950
    surface: "#0f172a", // industrial-900
    surfaceHover: "#1e293b", // industrial-800
    text: "#dcfce7", // matcha-100
    textMuted: "#86efac", // matcha-300
    border: "#334155", // industrial-700
    accent: "#4ade80", // matcha-400
  },
};

export const industrialTheme = {
  light: {
    primary: "#0f172a", // industrial-900
    primaryHover: "#1e293b", // industrial-800
    secondary: "#64748b", // industrial-500
    background: "#f8fafc", // industrial-50
    surface: "#ffffff",
    surfaceHover: "#f1f5f9", // industrial-100
    text: "#0f172a", // industrial-900
    textMuted: "#64748b", // industrial-500
    border: "#e2e8f0", // industrial-200
    accent: "#475569", // industrial-600
  },
  dark: {
    primary: "#f8fafc", // industrial-50
    primaryHover: "#e2e8f0", // industrial-200
    secondary: "#64748b", // industrial-500
    background: "#020617", // industrial-950
    surface: "#0a0f1a", // industrial-925
    surfaceHover: "#0f172a", // industrial-900
    text: "#f8fafc", // industrial-50
    textMuted: "#94a3b8", // industrial-400
    border: "#334155", // industrial-700
    accent: "#cbd5e1", // industrial-300
  },
};

export type ThemeName = "matcha" | "industrial";

export function applyTheme(theme: ThemeName, mode: "light" | "dark" = "dark") {
  const themeConfig = theme === "matcha" ? matchaTheme : industrialTheme;
  const colors = themeConfig[mode];

  if (typeof document !== "undefined") {
    const root = document.documentElement;
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--theme-${key}`, value);
    });
  }
}
