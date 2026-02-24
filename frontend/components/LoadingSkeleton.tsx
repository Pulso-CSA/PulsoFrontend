/**
 * LoadingSkeleton – Indicador de carregamento durante treino ou previsão
 */

import React from 'react';
import { colors, typography, borderRadius } from '../design-system/tokens';

export interface LoadingSkeletonProps {
  message?: string;
  variant?: 'chat' | 'metrics' | 'charts';
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  message = 'Processando...',
  variant = 'chat',
}) => {
  return (
    <div
      style={{
        padding: '1.5rem',
        borderRadius: borderRadius.lg,
        background: colors.bgCard,
        animation: 'pulse 1.5s ease-in-out infinite',
      }}
    >
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <div
          style={{
            width: 24,
            height: 24,
            borderRadius: '50%',
            border: `2px solid ${colors.accent}`,
            borderTopColor: 'transparent',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
        <span
          style={{
            fontSize: typography.fontSize.sm,
            color: colors.textSecondary,
          }}
        >
          {message}
        </span>
      </div>
      {variant === 'metrics' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '1rem',
            marginTop: '1.5rem',
          }}
        >
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                height: 80,
                borderRadius: borderRadius.md,
                background: colors.bgElevated,
                opacity: 0.6,
              }}
            />
          ))}
        </div>
      )}
      {variant === 'charts' && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            marginTop: '1.5rem',
          }}
        >
          {[1, 2].map((i) => (
            <div
              key={i}
              style={{
                height: 200,
                borderRadius: borderRadius.md,
                background: colors.bgElevated,
                opacity: 0.6,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};
