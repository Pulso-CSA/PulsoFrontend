/**
 * ChatBubble – Bolha de mensagem elegante para chat de Inteligência de Dados
 * Suporta mensagens do usuário e do sistema com estilo profissional
 */

import React from 'react';
import { colors, typography, borderRadius, shadows, transitions } from '../design-system/tokens';

export interface ChatBubbleProps {
  content: string;
  isUser?: boolean;
  timestamp?: string;
  children?: React.ReactNode;
  className?: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  content,
  isUser = false,
  timestamp,
  children,
  className = '',
}) => {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '1rem',
      }}
    >
      <div
        style={{
          maxWidth: '85%',
          padding: '1rem 1.25rem',
          borderRadius: borderRadius.lg,
          background: isUser ? colors.accent : colors.bgCard,
          color: colors.textPrimary,
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
            fontFamily: typography.fontFamily.sans,
            fontSize: typography.fontSize.base,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {content}
        </div>
        {children && (
          <div style={{ marginTop: '1rem' }}>{children}</div>
        )}
        {timestamp && (
          <div
            style={{
              marginTop: '0.5rem',
              fontSize: typography.fontSize.xs,
              color: colors.textSecondary,
              opacity: 0.9,
            }}
          >
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
};
