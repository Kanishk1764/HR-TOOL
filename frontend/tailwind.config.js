/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "#e2e8f0",
        background: "#f8fafc",
        card: "#ffffff",
        primary: {
          DEFAULT: "#0f172a",
          foreground: "#f8fafc",
        },
        muted: {
          DEFAULT: "#64748b",
          foreground: "#94a3b8",
        },
        accent: {
          DEFAULT: "#2563eb",
          foreground: "#ffffff",
        }
      },
    },
  },
  plugins: [],
};
