/**
 * ModelsTable – Tabela de modelos comparados com ordenação e destaque no modelo escolhido
 * Colunas: Modelo, Acurácia, AUC, Recall, Prec., F1, Kappa, MCC
 */

import React, { useState } from 'react';
import { colors, typography, borderRadius, shadows } from '../design-system/tokens';

export interface ModelRow {
  modelo: string;
  acuracia?: number;
  auc?: number;
  recall?: number;
  precisao?: number;
  f1?: number;
  kappa?: number;
  mcc?: number;
}

export interface ModelsTableProps {
  models: ModelRow[];
  selectedModel?: string;
}

const COLUMNS: { key: keyof ModelRow; label: string }[] = [
  { key: 'modelo', label: 'Modelo' },
  { key: 'acuracia', label: 'Acurácia' },
  { key: 'auc', label: 'AUC' },
  { key: 'recall', label: 'Recall' },
  { key: 'precisao', label: 'Prec.' },
  { key: 'f1', label: 'F1' },
  { key: 'kappa', label: 'Kappa' },
  { key: 'mcc', label: 'MCC' },
];

const normalizeKey = (row: ModelRow, key: keyof ModelRow): number | undefined => {
  const v = row[key];
  if (typeof v === 'number') return v;
  const aliases: Record<string, string[]> = {
    acuracia: ['Acurácia', 'acuracia'],
    auc: ['AUC', 'auc'],
    recall: ['Recall', 'recall'],
    precisao: ['Prec', 'Prec.', 'precisao'],
    f1: ['F1', 'f1'],
    kappa: ['Kappa', 'kappa'],
    mcc: ['MCC', 'mcc'],
  };
  const keys = aliases[key as string];
  if (keys) {
    for (const k of keys) {
      const val = (row as Record<string, unknown>)[k];
      if (typeof val === 'number') return val;
    }
  }
  return undefined;
};

const getMetricColor = (val: number) => {
  if (val >= 80) return colors.metricHigh;
  if (val >= 60) return colors.metricMedium;
  return colors.metricLow;
};

export const ModelsTable: React.FC<ModelsTableProps> = ({ models, selectedModel }) => {
  const [sortBy, setSortBy] = useState<keyof ModelRow>('acuracia');
  const [sortDesc, setSortDesc] = useState(true);

  const handleSort = (key: keyof ModelRow) => {
    if (sortBy === key) setSortDesc(!sortDesc);
    else setSortBy(key);
  };

  const sorted = [...models].sort((a, b) => {
    const va = sortBy === 'modelo' ? 0 : (normalizeKey(a, sortBy) ?? 0);
    const vb = sortBy === 'modelo' ? 0 : (normalizeKey(b, sortBy) ?? 0);
    return sortDesc ? (vb - va) : (va - vb);
  });

  return (
    <div
      style={{
        marginTop: '1rem',
        overflow: 'auto',
        borderRadius: borderRadius.md,
        background: colors.bgCard,
        boxShadow: shadows.card,
      }}
    >
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
        Modelos comparados
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {COLUMNS.map(({ key, label }) => (
              <th
                key={key}
                onClick={() => key !== 'modelo' && handleSort(key)}
                style={{
                  padding: '0.75rem 1rem',
                  textAlign: 'left',
                  fontSize: typography.fontSize.xs,
                  fontWeight: typography.fontWeight.semibold,
                  color: colors.textSecondary,
                  textTransform: 'uppercase',
                  cursor: key !== 'modelo' ? 'pointer' : 'default',
                  borderBottom: `1px solid ${colors.bgElevated}`,
                }}
              >
                {label}
                {key === sortBy && (sortDesc ? ' ↓' : ' ↑')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => {
            const isSelected = row.modelo === selectedModel;
            return (
              <tr
                key={row.modelo + i}
                style={{
                  background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  borderLeft: isSelected ? `3px solid ${colors.accent}` : '3px solid transparent',
                }}
              >
                {COLUMNS.map(({ key }) => {
                  const val = key === 'modelo' ? row[key] : (normalizeKey(row, key) ?? row[key]);
                  const isNum = typeof val === 'number';
                  const display = isNum ? `${val}%` : val;
                  const color = isNum ? getMetricColor(val) : colors.textPrimary;

                  return (
                    <td
                      key={key}
                      style={{
                        padding: '0.75rem 1rem',
                        fontSize: typography.fontSize.sm,
                        color: color,
                        fontFamily: isNum ? typography.fontFamily.mono : undefined,
                        borderBottom: `1px solid ${colors.bgElevated}`,
                      }}
                    >
                      {display ?? '–'}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
