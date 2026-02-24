/**
 * MetricCard – Card de métrica de ML com barra de progresso e badge de cor
 * Exibe Precisão, Recall, F1, Acurácia, AUC, Kappa, MCC
 */

import React from 'react';
import { colors, typography, borderRadius, shadows, transitions } from '../design-system/tokens';

export interface MetricCardProps {
  label: string;
  value: string | number;
  percent?: number;
  variant?: 'high' | 'medium' | 'low' | 'neutral';
  icon?: React.ReactNode;
}

const getMetricColor = (variant: MetricCardProps['variant']) => {
  switch (variant) {
    case 'high': return colors.metricHigh;
    case 'medium': return colors.metricMedium;
    case 'low': return colors.metricLow;
    default: return colors.accent;
  }
};

const getVariantFromPercent = (percent: number): MetricCardProps['variant'] => {
  if (percent >= 80) return 'high';
  if (percent >= 60) return 'medium';
  return 'low';
};

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  percent,
  variant,
  icon,
}) => {
  const resolvedVariant = variant ?? (percent != null ? getVariantFromPercent(percent) : 'neutral');
  const accentColor = getMetricColor(resolvedVariant);

  return (
    <div
      style={{
        padding: '1rem 1.25rem',
        borderRadius: borderRadius.md,
        background: colors.bgCard,
        boxShadow: shadows.card,
        transition: `transform ${transitions.normal}, box-shadow ${transitions.normal}`,
        minWidth: '140px',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = shadows.cardHover;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = shadows.card;
      }}
    >
      {icon && (
        <div style={{ marginBottom: '0.5rem', opacity: 0.8 }}>{icon}</div>
      )}
      <div
        style={{
          fontSize: typography.fontSize.xs,
          fontWeight: typography.fontWeight.medium,
          color: colors.textSecondary,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: typography.fontSize['2xl'],
          fontWeight: typography.fontWeight.bold,
          fontFamily: typography.fontFamily.mono,
          color: accentColor,
          marginTop: '0.25rem',
        }}
      >
        {typeof value === 'number' ? `${value}%` : value}
      </div>
      {percent != null && (
        <div
          style={{
            marginTop: '0.5rem',
            height: '4px',
            borderRadius: '2px',
            background: colors.bgElevated,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, percent)}%`,
              background: accentColor,
              borderRadius: '2px',
              transition: `width ${transitions.slow}`,
            }}
          />
        </div>
      )}
    </div>
  );
};
