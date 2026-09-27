/**
 * NEXORA ATLAS - Design System Tokens
 * Specification 3.1.0: "The Technology Financial Intelligence Command Center"
 * SOBER, HIGH-DENSITY, ENTERPRISE FINOPS PALETTE
 */

export const colors = {
  canvas: '#080B10',
  surface: '#0F141C',
  elevated: '#141B27',
  overlay: '#1A2234',
  border: '#1E2638',
  borderSoft: '#17202D',
  primary: '#0EA5E9',
  info: '#38BDF8',
  success: '#10B981',
  warning: '#F59E0B',
  critical: '#EF4444',
  text: {
    primary: '#F1F5F9',
    secondary: '#94A3B8',
    muted: '#64748B',
    disabled: '#475569',
  },
  epistemic: {
    observed: { bg: '#1E293B', text: '#94A3B8', border: '#334155' },
    derived: { bg: '#0C2A4A', text: '#7DD3FC', border: '#0284C7' },
    inferred: { bg: '#3D2206', text: '#FCD34D', border: '#D97706' },
    assumed: { bg: '#281347', text: '#C4B5FD', border: '#7C3AED' },
    projected: { bg: '#082F49', text: '#38BDF8', border: '#0284C7' },
    notAvailable: { bg: '#181E29', text: '#64748B', border: '#334155' },
  },
} as const;

export const fonts = {
  sans: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  mono: '"JetBrains Mono", "Fira Code", monospace',
} as const;
