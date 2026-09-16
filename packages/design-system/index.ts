/**
 * NEXORA ATLAS - Design System Tokens
 * Near-black Bloomberg/FinOps aesthetic palette
 */

export const colors = {
  background: '#080B10',
  surface: '#0E131F',
  elevated: '#161D2E',
  border: '#1E293B',
  borderMuted: 'rgba(255, 255, 255, 0.08)',
  primary: '#38BDF8', // Sky 400
  primaryHover: '#0EA5E9', // Sky 500
  success: '#10B981', // Emerald 500
  warning: '#F59E0B', // Amber 500
  critical: '#EF4444', // Rose 500
  text: {
    primary: '#F8FAFC',
    secondary: '#94A3B8',
    muted: '#64748B',
  },
} as const;

export const fonts = {
  sans: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  mono: '"JetBrains Mono", "Fira Code", monospace',
} as const;
