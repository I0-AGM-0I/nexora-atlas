import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        atlas: {
          bg: '#080B10',
          surface: '#0E131F',
          elevated: '#161D2E',
          border: '#1E293B',
          primary: '#38BDF8',
          success: '#10B981',
          warning: '#F59E0B',
          critical: '#EF4444',
          muted: '#64748B',
          text: '#F8FAFC',
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
