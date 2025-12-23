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
      },
    },
  },
  plugins: [],
}

