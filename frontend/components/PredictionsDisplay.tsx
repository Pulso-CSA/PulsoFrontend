/**
 * PredictionsDisplay – Exibição de previsões com badge, distribuição e tabela
 * Integra com previsoes, distribuicao_previsoes e exemplos_previsao da API
 */

import React from 'react';
import { colors, typography, borderRadius, shadows } from '../design-system/tokens';

export interface PredictionsDisplayProps {
  previsoes: string[];
  distribuicao?: Record<string, number>;
  exemplos?: Array<{ indice: number; previsao: string }>;
  clientIds?: string[];
}

export const PredictionsDisplay: React.FC<PredictionsDisplayProps> = ({
  previsoes,
  distribuicao,
  exemplos = [],
  clientIds = [],
}) => {
  const dist = distribuicao ?? previsoes.reduce((acc, p) => {
    acc[p] = (acc[p] + 1) || 1;
    return acc;
  }, {} as Record<string, number>);

  const total = previsoes.length;
  const yesCount = dist['Yes'] ?? dist['yes'] ?? 0;
  const noCount = dist['No'] ?? dist['no'] ?? total - yesCount;

  const sample = exemplos.length > 0 ? exemplos : previsoes.slice(0, 20).map((p, i) => ({ indice: i, previsao: p }));

  return (
    <div style={{ marginTop: '1rem' }}>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '1rem',
        }}
      >
        <span
          style={{
            padding: '0.35rem 0.75rem',
            borderRadius: borderRadius.sm,
            background: colors.bgCard,
            fontSize: typography.fontSize.sm,
            color: colors.textSecondary,
          }}
        >
          {total} previsões
        </span>
        <span
          style={{
            padding: '0.35rem 0.75rem',
            borderRadius: borderRadius.sm,
            background: colors.success,
            color: colors.textPrimary,
            fontSize: typography.fontSize.sm,
            fontWeight: typography.fontWeight.medium,
          }}
        >
          {noCount} No
        </span>
        <span
          style={{
            padding: '0.35rem 0.75rem',
            borderRadius: borderRadius.sm,
            background: colors.warning,
            color: colors.textPrimary,
            fontSize: typography.fontSize.sm,
            fontWeight: typography.fontWeight.medium,
          }}
        >
          {yesCount} Yes
        </span>
      </div>

      {sample.length > 0 && (
        <div
          style={{
            borderRadius: borderRadius.md,
            background: colors.bgCard,
            boxShadow: shadows.card,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '0.75rem 1rem',
              fontSize: typography.fontSize.xs,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textSecondary,
              textTransform: 'uppercase',
              borderBottom: `1px solid ${colors.bgElevated}`,
            }}
          >
            Amostra
          </div>
          <div style={{ maxHeight: '200px', overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th
                    style={{
                      padding: '0.5rem 1rem',
                      textAlign: 'left',
                      fontSize: typography.fontSize.xs,
                      color: colors.textMuted,
                    }}
                  >
                    #
                  </th>
                  {clientIds.length > 0 && (
                    <th
                      style={{
                        padding: '0.5rem 1rem',
                        textAlign: 'left',
                        fontSize: typography.fontSize.xs,
                        color: colors.textMuted,
                      }}
                    >
                      ID
                    </th>
                  )}
                  <th
                    style={{
                      padding: '0.5rem 1rem',
                      textAlign: 'left',
                      fontSize: typography.fontSize.xs,
                      color: colors.textMuted,
                    }}
                  >
                    Previsão
                  </th>
                </tr>
              </thead>
              <tbody>
                {sample.map((ex, i) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom: i < sample.length - 1 ? `1px solid ${colors.bgElevated}` : 'none',
                    }}
                  >
                    <td
                      style={{
                        padding: '0.5rem 1rem',
                        fontSize: typography.fontSize.sm,
                        color: colors.textSecondary,
                        fontFamily: typography.fontFamily.mono,
                      }}
                    >
                      {ex.indice}
                    </td>
                    {clientIds.length > 0 && (
                      <td
                        style={{
                          padding: '0.5rem 1rem',
                          fontSize: typography.fontSize.sm,
                          color: colors.textSecondary,
                          fontFamily: typography.fontFamily.mono,
                        }}
                      >
                        {clientIds[ex.indice] ?? '–'}
                      </td>
                    )}
                    <td
                      style={{
                        padding: '0.5rem 1rem',
                        fontSize: typography.fontSize.sm,
                      }}
                    >
                      <span
                        style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: borderRadius.sm,
                          background: ex.previsao.toLowerCase() === 'yes' ? colors.warning : colors.success,
                          color: colors.textPrimary,
                          fontSize: typography.fontSize.xs,
                          fontWeight: typography.fontWeight.medium,
                        }}
                      >
                        {ex.previsao}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
