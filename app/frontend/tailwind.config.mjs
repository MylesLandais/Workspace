/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        gray: {
          950: '#0a0a0a',
        },
        theme: {
          'bg-primary': 'var(--theme-bg-primary)',
          'bg-secondary': 'var(--theme-bg-secondary)',
          'border-primary': 'var(--theme-border-primary)',
          'text-primary': 'var(--theme-text-primary)',
          'text-secondary': 'var(--theme-text-secondary)',
          'accent-primary': 'var(--theme-accent-primary)',
          'accent-secondary': 'var(--theme-accent-secondary)',
          'accent-tertiary': 'var(--theme-accent-tertiary)',
          'accent-alert': 'var(--theme-accent-alert)',
        },
        // Bunny theme colors - map to existing theme variables
        app: {
          bg: 'var(--theme-bg-primary)',
          surface: 'var(--theme-bg-secondary)',
          'surface-hover': 'var(--theme-bg-secondary)',
          text: 'var(--theme-text-primary)',
          muted: 'var(--theme-text-secondary)',
          accent: 'var(--theme-accent-primary)',
          'accent-hover': 'var(--theme-accent-secondary)',
          'accent-light': 'var(--theme-accent-tertiary)',
          border: 'var(--theme-border-primary)',
        },
      },
    },
  },
  plugins: [],
}

