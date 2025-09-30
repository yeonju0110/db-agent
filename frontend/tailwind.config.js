/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          primary: {
            DEFAULT: '#2563EB',
            light: '#EFF6FF',
            dark: '#1E40AF',
          },
          status: {
            success: '#10B981',
            'success-light': '#D1FAE5',
            warning: '#F59E0B',
            'warning-light': '#FEF3C7',
            error: '#EF4444',
            'error-light': '#FEE2E2',
          },
        },
      },
    },
    plugins: [],
  }