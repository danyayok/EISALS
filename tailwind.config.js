/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/**/*.py"
  ],
  theme: {
    extend: {
        fontFamily: {
            sans: ['Jost', "Arial", "sans-serif"]
        }
    },
  },
  plugins: [],
}
