/**
 * Design System – Inteligência de Dados
 * Tokens de cores, tipografia e espaçamento para interface elegante e profissional
 */

export const colors = {
  // Fundos
  bgPrimary: '#1a1625',
  bgCard: '#2d2640',
  bgCardHover: '#352d4a',
  bgElevated: '#3d3554',

  // Destaques
  accent: '#3b82f6',
  accentCyan: '#06b6d4',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',

  // Texto
  textPrimary: '#f1f5f9',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',

  // Métricas (badges)
  metricHigh: '#22c55e',
  metricMedium: '#f59e0b',
  metricLow: '#ef4444',
} as const;

export const typography = {
  fontFamily: {
    sans: "'Inter', 'DM Sans', system-ui, sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', monospace",
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
} as const;

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '2.5rem',
} as const;

export const borderRadius = {
  sm: '6px',
  md: '10px',
  lg: '14px',
  xl: '20px',
} as const;

export const shadows = {
  card: '0 2px 8px rgba(0, 0, 0, 0.2)',
  cardHover: '0 4px 16px rgba(0, 0, 0, 0.3)',
  elevated: '0 8px 24px rgba(0, 0, 0, 0.35)',
} as const;

export const transitions = {
  fast: '0.15s ease',
  normal: '0.2s ease',
  slow: '0.3s ease',
} as const;
