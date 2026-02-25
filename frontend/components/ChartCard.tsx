/**
 * ChartCard – Card de gráfico com título, insight e link "Vantagens e desvantagens" colapsável
 * Integra com graficos_metadados e graficos_dados da API
 */

import React, { useState } from 'react';
import { colors, typography, borderRadius, shadows, transitions } from '../design-system/tokens';

export interface ChartCardProps {
  title: string;
  insight?: string;
  children: React.ReactNode;
  vantagens?: string[];
  desvantagens?: string[];
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  insight,
  children,
  vantagens = [],
  desvantagens = [],
}) => {
  const [showVantagens, setShowVantagens] = useState(false);
  const hasVantagens = vantagens.length > 0 || desvantagens.length > 0;

  return (
    <div
      style={{
        padding: '1.25rem',
        borderRadius: borderRadius.lg,
        background: colors.bgCard,
        boxShadow: shadows.card,
        transition: `transform ${transitions.normal}, box-shadow ${transitions.normal}`,
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
      <div
        style={{
          fontSize: typography.fontSize.lg,
          fontWeight: typography.fontWeight.semibold,
          color: colors.textPrimary,
          marginBottom: '1rem',
        }}
      >
        {title}
      </div>
      <div style={{ minHeight: '200px' }}>{children}</div>
      {insight && (
        <div
          style={{
            marginTop: '1rem',
            fontSize: typography.fontSize.sm,
            color: colors.textSecondary,
            lineHeight: 1.5,
          }}
        >
          {insight}
        </div>
      )}
      {hasVantagens && (
        <div style={{ marginTop: '1rem' }}>
          <button
            onClick={() => setShowVantagens(!showVantagens)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'none',
              border: 'none',
              color: colors.accent,
              fontSize: typography.fontSize.sm,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            <span>ⓘ</span>
            Vantagens e desvantagens
          </button>
          {showVantagens && (
            <div
              style={{
                marginTop: '0.75rem',
                padding: '1rem',
                background: colors.bgElevated,
                borderRadius: borderRadius.sm,
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary,
              }}
            >
              {vantagens.length > 0 && (
                <div style={{ marginBottom: '0.5rem' }}>
                  <strong style={{ color: colors.success }}>Vantagens:</strong> {vantagens.join('; ')}
                </div>
              )}
              {desvantagens.length > 0 && (
                <div>
                  <strong style={{ color: colors.warning }}>Desvantagens:</strong> {desvantagens.join('; ')}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
