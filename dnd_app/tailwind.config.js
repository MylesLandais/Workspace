// See the Tailwind default theme values
// https://github.com/tailwindlabs/tailwindcss/blob/master/stubs/defaultConfig.stub.js

module.exports = {
  content: [
    "./js/**/*.ts",
    "./js/**/*.js",
    "../lib/*_web.ex",
    "../lib/*_web/**/*.*ex"
  ],
  theme: {
    extend: {
      colors: {
        // Canvas (Backgrounds)
        sand: {
          50: '#F9F8F6',
          100: '#F0EEE9',
        },
        // Ink (Text)
        ink: {
          500: '#6B6B6B',
          900: '#1A1A1A',
        },
        // Accents (Functional)
        forest: {
          600: '#2F4F4F',
        },
        clay: {
          500: '#C06C54',
        },
        stone: {
          300: '#D6D3D1',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Fraunces', 'serif'],
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
      },
      borderRadius: {
        xl: '12px',
      },
    },
  },
  plugins: [],
}





