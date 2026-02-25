/**
 * ConfusionMatrix – Matriz de confusão como heatmap com labels TN, FP, FN, TP
 * Design elegante com cores por intensidade e tooltips
 */

import React, { useState } from 'react';
import { colors, typography, borderRadius, shadows } from '../design-system/tokens';

export interface ConfusionMatrixProps {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
  labels?: { negative?: string; positive?: string };
}

const CELL_TOOLTIPS: Record<string, string> = {
  TN: 'Verdadeiro Negativo: previsto Não, real Não',
  FP: 'Falso Positivo: previsto Sim, real Não',
  FN: 'Falso Negativo: previsto Não, real Sim',
  TP: 'Verdadeiro Positivo: previsto Sim, real Sim',
};

export const ConfusionMatrix: React.FC<ConfusionMatrixProps> = ({
  tn,
  fp,
  fn,
  tp,
  labels = {},
}) => {
  const neg = labels.negative ?? 'Não';
  const pos = labels.positive ?? 'Sim';

  const cells = [
    { value: tn, label: 'TN', desc: 'Previsto Não / Real Não', color: colors.success },
    { value: fp, label: 'FP', desc: 'Previsto Sim / Real Não', color: colors.warning },
    { value: fn, label: 'FN', desc: 'Previsto Não / Real Sim', color: colors.warning },
    { value: tp, label: 'TP', desc: 'Previsto Sim / Real Sim', color: colors.success },
  ];

  const maxVal = Math.max(tn, fp, fn, tp);

  return (
    <div style={{ marginTop: '1rem' }}>
      <div
        style={{
          fontSize: typography.fontSize.sm,
          color: colors.textSecondary,
          marginBottom: '0.75rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}
      >
        <span>Matriz de confusão</span>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.5rem',
          maxWidth: '280px',
        }}
      >
        {cells.map(({ value, label, desc, color }) => (
          <Cell key={label} value={value} label={label} color={color} tooltip={CELL_TOOLTIPS[label] || desc} />
        ))}
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.5rem',
          maxWidth: '280px',
          marginTop: '0.5rem',
          fontSize: typography.fontSize.xs,
          color: colors.textSecondary,
          textAlign: 'center',
        }}
      >
        <span>TN</span>
        <span>FP</span>
        <span>FN</span>
        <span>TP</span>
      </div>
      <div
        style={{
          marginTop: '0.75rem',
          fontSize: typography.fontSize.xs,
          color: colors.textMuted,
        }}
      >
        Real: {neg} / {pos} • Previsto: {neg} / {pos}
      </div>
    </div>
  );
};

const Cell: React.FC<{ value: number; label: string; color: string; tooltip: string }> = ({
  value,
  label,
  color,
  tooltip,
}) => {
  const [hover, setHover] = useState(false);

  return (
    <div
      title={tooltip}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        padding: '1rem',
        borderRadius: borderRadius.md,
        background: color,
        color: colors.textPrimary,
        fontSize: typography.fontSize.xl,
        fontWeight: typography.fontWeight.bold,
        fontFamily: typography.fontFamily.mono,
        textAlign: 'center',
        boxShadow: hover ? shadows.cardHover : shadows.card,
        transform: hover ? 'scale(1.02)' : 'scale(1)',
        transition: 'all 0.2s ease',
        cursor: 'help',
      }}
    >
      {value}
    </div>
  );
};
