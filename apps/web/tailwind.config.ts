import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        atlas: {
          bg: '#080B10',
          canvas: '#080B10',
          surface: '#0F141C',
          elevated: '#141B27',
          overlay: '#1A2234',
          border: '#1E2638',
          'border-soft': '#17202D',
          primary: '#0EA5E9',
          info: '#38BDF8',
          success: '#10B981',
          warning: '#F59E0B',
          critical: '#EF4444',
          muted: '#64748B',
          disabled: '#475569',
          text: '#F1F5F9',
          'text-primary': '#F1F5F9',
          secondary: '#94A3B8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(0, 0, 0, 0.4)',
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -2px rgba(0, 0, 0, 0.5)',
      },
    },
  },
  plugins: [],
} satisfies Config;
