/**
 * IDResponseView – Componente principal que renderiza a resposta do chat ID
 * Consome IDChatOutput da API e exibe texto, métricas, matriz, modelos e gráficos
 */

import React, { useState } from 'react';
import { ChatBubble } from './ChatBubble';
import { MetricCard } from './MetricCard';
import { ConfusionMatrix } from './ConfusionMatrix';
import { ChartCard } from './ChartCard';
import { ModelsTable } from './ModelsTable';
import { PredictionsDisplay } from './PredictionsDisplay';
import { colors, typography, spacing, transitions } from '../design-system/tokens';

export interface IDResponseViewProps {
  resposta_texto: string;
  analise_estatistica?: {
    graficos_metadados?: Array<{
      titulo?: string;
      insight_especifico?: string;
      vantagens?: string[];
      desvantagens?: string[];
    }>;
    graficos_dados?: Array<{
      labels?: string[];
      values?: number[];
      x?: number[];
      y?: number[];
    }>;
  };
  modelo_ml?: {
    modelo_escolhido?: string;
    resultados?: Record<string, number>;
    matriz_confusao?: { tn?: number; fp?: number; fn?: number; tp?: number } | number[][];
    modelos_comparados?: Array<Record<string, unknown>>;
  };
  previsoes?: string[];
  distribuicao_previsoes?: Record<string, number>;
  exemplos_previsao?: Array<{ indice: number; previsao: string }>;
  timestamp?: string;
  /** Componente customizado para renderizar gráficos (Chart.js, Recharts, etc.) */
  ChartRenderer?: React.ComponentType<ChartRendererProps>;
}

export interface ChartRendererProps {
  tipo: string;
  titulo: string;
  labels?: string[];
  values?: number[];
  x?: number[];
  y?: number[];
}

export const IDResponseView: React.FC<IDResponseViewProps> = ({
  resposta_texto,
  analise_estatistica,
  modelo_ml,
  previsoes,
  distribuicao_previsoes,
  exemplos_previsao,
  timestamp,
  ChartRenderer,
}) => {
  const [chartIndex, setChartIndex] = useState(0);

  const graficos = analise_estatistica?.graficos_metadados ?? [];
  const graficosDados = analise_estatistica?.graficos_dados ?? [];
  const totalCharts = graficos.length;

  const resultados = modelo_ml?.resultados ?? {};
  const matriz = modelo_ml?.matriz_confusao;
  const modelosComparados = modelo_ml?.modelos_comparados ?? [];

  const tn = Array.isArray(matriz)
    ? matriz[0]?.[0] ?? 0
    : matriz?.tn ?? 0;
  const fp = Array.isArray(matriz)
    ? matriz[0]?.[1] ?? 0
    : matriz?.fp ?? 0;
  const fn = Array.isArray(matriz)
    ? matriz[1]?.[0] ?? 0
    : matriz?.fn ?? 0;
  const tp = Array.isArray(matriz)
    ? matriz[1]?.[1] ?? 0
    : matriz?.tp ?? 0;

  const metricLabels: Record<string, string> = {
    precisao: 'PRECISÃO',
    recall: 'RECALL',
    f1: 'F1',
    acuracia: 'ACURÁCIA',
    auc: 'AUC',
    kappa: 'KAPPA',
    mcc: 'MCC',
  };

  const getNum = (m: Record<string, unknown>, ...keys: string[]) => {
    for (const k of keys) {
      const v = m[k];
      if (typeof v === 'number') return v;
    }
    return undefined;
  };

  const modelRows = modelosComparados.map((m: Record<string, unknown>) => ({
    modelo: String(m.modelo ?? m.Model ?? m.Modelo ?? '–'),
    acuracia: getNum(m, 'acuracia', 'Acurácia', 'Acuracia'),
    auc: getNum(m, 'auc', 'AUC'),
    recall: getNum(m, 'recall', 'Recall'),
    precisao: getNum(m, 'precisao', 'Prec', 'Prec.', 'Precisão', 'Precisao'),
    f1: getNum(m, 'f1', 'F1'),
    kappa: getNum(m, 'kappa', 'Kappa'),
    mcc: getNum(m, 'mcc', 'MCC'),
  }));

  return (
    <ChatBubble content={resposta_texto} isUser={false} timestamp={timestamp}>
      {/* Modelo treinado */}
      {modelo_ml?.modelo_escolhido && modelo_ml.modelo_escolhido !== 'N/A' && (
        <div style={{ marginTop: spacing.lg }}>
          <div
            style={{
              fontSize: typography.fontSize.sm,
              color: colors.textSecondary,
              marginBottom: spacing.sm,
            }}
          >
            Modelo treinado
          </div>
          <div
            style={{
              padding: spacing.sm,
              borderRadius: '8px',
              background: colors.bgElevated,
              display: 'inline-block',
              color: colors.accent,
              fontWeight: typography.fontWeight.semibold,
            }}
          >
            {modelo_ml.modelo_escolhido}
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: spacing.md,
              marginTop: spacing.md,
            }}
          >
            {Object.entries(resultados).map(([key, val]) => {
              if (typeof val !== 'number') return null;
              const label = metricLabels[key.toLowerCase()] ?? key;
              return (
                <MetricCard
                  key={key}
                  label={label}
                  value={val}
                  percent={val}
                />
              );
            })}
          </div>
          {(tn || fp || fn || tp) > 0 && (
            <ConfusionMatrix tn={tn} fp={fp} fn={fn} tp={tp} />
          )}
        </div>
      )}

      {/* Modelos comparados */}
      {modelRows.length > 0 && (
        <ModelsTable
          models={modelRows}
          selectedModel={modelo_ml?.modelo_escolhido as string}
        />
      )}

      {/* Previsões */}
      {previsoes && previsoes.length > 0 && (
        <PredictionsDisplay
          previsoes={previsoes}
          distribuicao={distribuicao_previsoes}
          exemplos={exemplos_previsao}
        />
      )}

      {/* Gráficos */}
      {totalCharts > 0 && (
        <div style={{ marginTop: spacing.xl }}>
          <div
            style={{
              fontSize: typography.fontSize.sm,
              color: colors.textSecondary,
              marginBottom: spacing.md,
            }}
          >
            Gráficos disponíveis: distribuições, contagens e dispersões.
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: spacing.lg,
            }}
          >
            {[chartIndex, chartIndex + 1].filter((i) => i < totalCharts).map((i) => {
              const meta = graficos[i];
              const dados = graficosDados[i] ?? {};
              const tipo = (meta?.titulo?.toLowerCase().includes('dispers') ? 'dispersao' : 'barra') as string;

              return (
                <ChartCard
                  key={i}
                  title={meta?.titulo ?? `Gráfico ${i + 1}`}
                  insight={meta?.insight_especifico}
                  vantagens={meta?.vantagens}
                  desvantagens={meta?.desvantagens}
                >
                  {ChartRenderer ? (
                    <ChartRenderer
                      tipo={tipo}
                      titulo={meta?.titulo ?? ''}
                      labels={dados.labels}
                      values={dados.values}
                      x={dados.x}
                      y={dados.y}
                    />
                  ) : (
                    <PlaceholderChart tipo={tipo} dados={dados} />
                  )}
                </ChartCard>
              );
            })}
          </div>
          {totalCharts > 1 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: spacing.md,
                marginTop: spacing.lg,
              }}
            >
              <button
                onClick={() => setChartIndex(Math.max(0, chartIndex - 1))}
                disabled={chartIndex === 0}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  background: colors.bgCard,
                  color: colors.textPrimary,
                  border: 'none',
                  cursor: chartIndex === 0 ? 'not-allowed' : 'pointer',
                  opacity: chartIndex === 0 ? 0.5 : 1,
                }}
              >
                &lt;
              </button>
              <span style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>
                Gráfico {chartIndex + 1} de {totalCharts}
              </span>
              <button
                onClick={() => setChartIndex(Math.min(totalCharts - 1, chartIndex + 1))}
                disabled={chartIndex >= totalCharts - 1}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  background: colors.bgCard,
                  color: colors.textPrimary,
                  border: 'none',
                  cursor: chartIndex >= totalCharts - 1 ? 'not-allowed' : 'pointer',
                  opacity: chartIndex >= totalCharts - 1 ? 0.5 : 1,
                }}
              >
                &gt;
              </button>
            </div>
          )}
        </div>
      )}
    </ChatBubble>
  );
};

const PlaceholderChart: React.FC<{ tipo: string; dados: Record<string, unknown> }> = ({ tipo, dados }) => {
  const labels = (dados.labels as string[]) ?? [];
  const values = (dados.values as number[]) ?? [];
  const max = Math.max(...values, 1);

  if (tipo === 'dispersao') {
    const x = (dados.x as number[]) ?? [];
    const y = (dados.y as number[]) ?? [];
    return (
      <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.textMuted }}>
        Use ChartRenderer com Recharts/Chart.js para dispersão
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 180, padding: '1rem 0' }}>
      {values.slice(0, 10).map((v, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: `${(v / max) * 100}%`,
            minHeight: 4,
            background: colors.accent,
            borderRadius: '4px 4px 0 0',
            transition: `height ${transitions.slow}`,
          }}
          title={labels[i] ? `${labels[i]}: ${v}` : String(v)}
        />
      ))}
    </div>
  );
};
