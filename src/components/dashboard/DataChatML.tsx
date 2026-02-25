import { useState } from "react";
import { Brain, BarChart3, GitCompare, Target, ChevronUp, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/** Cor da métrica por faixa (PulsoAPI): verde >= 80%, âmbar 60-80%, vermelho < 60% */
function getMetricColorClass(pct: number): string {
  if (pct >= 80) return "text-emerald-400";
  if (pct >= 60) return "text-amber-400";
  return "text-red-400";
}

function getMetricBarClass(pct: number): string {
  if (pct >= 80) return "bg-emerald-500/80";
  if (pct >= 60) return "bg-amber-500/80";
  return "bg-red-500/80";
}

/** Remove markdown cru (**texto**, listas) para exibição limpa */
export function stripMarkdown(text: string): string {
  if (!text || typeof text !== "string") return "";
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/^[-*]\s+/gm, "• ")
    .trim();
}

const METRIC_LABELS: Record<string, string> = {
  acuracia: "Acurácia",
  accuracy: "Acurácia",
  precisao: "Precisão",
  precision: "Precisão",
  prec: "Precisão",
  recall: "Recall",
  f1: "F1",
  auc: "AUC",
  kappa: "Kappa",
  mcc: "MCC",
  model: "Modelo",
  modelo: "Modelo",
  Model: "Modelo",
};

function formatMetricKey(key: string): string {
  const k = key.toLowerCase().replace(/\s/g, "_");
  return METRIC_LABELS[k] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatMetricValue(val: number): string {
  if (val >= 0 && val <= 1) return `${(val * 100).toFixed(1)}%`;
  return val.toFixed(2);
}

interface ModeloMLData {
  modelo_escolhido?: string;
  resultados?: Record<string, number>;
  matriz_confusao?: number[][];
  importancia_variaveis?: Array<{ variavel?: string; variable?: string; importancia?: number; importance?: number }>;
  metricas_negocio?: { total_amostra?: number; distribuicao_classe?: Record<string, number> };
  modelos_comparados?: Array<Record<string, string | number>>;
  previsoes_amostra?: unknown[];
}

interface DataChatMLProps {
  modeloMl: ModeloMLData;
  className?: string;
}

export function DataChatML({ modeloMl, className }: DataChatMLProps) {
  const [modelsSortBy, setModelsSortBy] = useState<string | null>(null);
  const [modelsSortDesc, setModelsSortDesc] = useState(true);

  const {
    modelo_escolhido,
    resultados,
    matriz_confusao,
    importancia_variaveis,
    metricas_negocio,
    modelos_comparados,
    previsoes_amostra,
  } = modeloMl;

  const hasData =
    modelo_escolhido ||
    (resultados && Object.keys(resultados).length > 0) ||
    (matriz_confusao && matriz_confusao.length > 0) ||
    (importancia_variaveis && importancia_variaveis.length > 0) ||
    (modelos_comparados && modelos_comparados.length > 0) ||
    (previsoes_amostra && previsoes_amostra.length > 0);

  if (!hasData) return null;

  return (
    <div className={cn("mt-6 space-y-6 animate-fade-in", className)}>
      {/* Modelo escolhido e métricas */}
      {(modelo_escolhido || (resultados && Object.keys(resultados).length > 0)) && (
        <div className="rounded-xl border border-white/10 bg-card/50 p-4 shadow-md transition-all duration-200 hover:shadow-lg hover:border-white/15">
          <h4 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
            <Brain className="h-4 w-4 text-primary" />
            Modelo treinado
          </h4>
          {modelo_escolhido && (
            <div className="mb-4 p-3 rounded-lg bg-primary/10 border border-primary/20">
              <p className="text-sm text-muted-foreground">Modelo</p>
              <p className="text-lg font-semibold font-mono text-primary">{modelo_escolhido}</p>
            </div>
          )}
          {resultados && Object.keys(resultados).length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.entries(resultados).map(([k, v]) => {
                const numVal = Number(v);
                const pct = numVal >= 0 && numVal <= 1 ? numVal * 100 : Math.min(100, numVal);
                const isPercentMetric = ["acuracia", "accuracy", "precisao", "precision", "recall", "f1", "auc"].includes(k.toLowerCase().replace(/\s/g, "_"));
                return (
                  <div
                    key={k}
                    className="rounded-lg bg-muted/30 p-3 border border-white/5 transition-all duration-200 hover:bg-muted/50 hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">{formatMetricKey(k)}</p>
                    <p className={cn("text-xl font-semibold font-mono tabular-nums mt-0.5", getMetricColorClass(pct))}>
                      {formatMetricValue(numVal)}
                    </p>
                    {isPercentMetric && (
                      <div className="mt-2 h-1 rounded-full bg-muted/50 overflow-hidden">
                        <div
                          className={cn("h-full rounded-full transition-all duration-500", getMetricBarClass(pct))}
                          style={{ width: `${Math.min(100, pct)}%` }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Matriz de confusão (PulsoAPI: TN/TP success, FP/FN warning) */}
      {matriz_confusao && matriz_confusao.length >= 2 && (() => {
        const tn = matriz_confusao[0]?.[0] ?? 0;
        const fp = matriz_confusao[0]?.[1] ?? 0;
        const fn = matriz_confusao[1]?.[0] ?? 0;
        const tp = matriz_confusao[1]?.[1] ?? 0;
        const cells = [
          { value: tn, label: "TN", tooltip: "Verdadeiro Negativo: previsto Não, real Não", color: "bg-emerald-600/80 text-white" },
          { value: fp, label: "FP", tooltip: "Falso Positivo: previsto Sim, real Não", color: "bg-amber-600/80 text-white" },
          { value: fn, label: "FN", tooltip: "Falso Negativo: previsto Não, real Sim", color: "bg-amber-600/80 text-white" },
          { value: tp, label: "TP", tooltip: "Verdadeiro Positivo: previsto Sim, real Sim", color: "bg-emerald-600/80 text-white" },
        ];
        return (
          <div className="rounded-xl border border-white/10 bg-card/50 p-4 shadow-md transition-all duration-200 hover:shadow-lg hover:border-white/15">
            <h4 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
              <Target className="h-4 w-4 text-primary" />
              Matriz de confusão
            </h4>
            <div className="inline-block">
              <div className="grid grid-cols-2 gap-2 w-48">
                {cells.map(({ value, label, tooltip, color }) => (
                  <TooltipProvider key={label}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div
                          className={cn(
                            "p-3 rounded-lg text-center font-mono text-lg font-semibold tabular-nums transition-all duration-200 hover:scale-[1.02] cursor-help",
                            color
                          )}
                        >
                          {value}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs">
                        {tooltip}
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Real: Não / Sim • Previsto: Não / Sim
              </p>
            </div>
          </div>
        );
      })()}

      {/* Importância de variáveis */}
      {importancia_variaveis && importancia_variaveis.length > 0 && (
        <div className="rounded-xl border border-white/10 bg-card/50 p-4 shadow-md transition-all duration-200 hover:shadow-lg hover:border-white/15">
          <h4 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-primary" />
            Importância de variáveis
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {[...importancia_variaveis]
              .sort((a, b) => (b.importancia ?? 0) - (a.importancia ?? 0))
              .slice(0, 10)
              .map((item, i) => {
                const imp = Number(item.importancia ?? item.importance ?? 0);
                const pct = imp >= 0 && imp <= 1 ? imp * 100 : imp;
                const varName = item.variavel ?? item.variable ?? "—";
                return (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-mono truncate max-w-[60%]" title={varName}>
                        {varName}
                      </span>
                      <span className="text-muted-foreground tabular-nums">{pct.toFixed(1)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted/50 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary/70 transition-all duration-500"
                        style={{ width: `${Math.min(100, pct)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Modelos comparados (PulsoAPI: ordenação clicável, badges de cor) */}
      {modelos_comparados && modelos_comparados.length > 0 && (() => {
        const cols = Object.keys(modelos_comparados[0] ?? {});
        const metricCols = cols.filter((c) => {
          const k = c.toLowerCase();
          return ["acuracia", "accuracy", "auc", "recall", "precisao", "prec", "f1", "kappa", "mcc"].some((m) => k.includes(m));
        });
        const getNum = (row: Record<string, string | number>, key: string): number => {
          const v = row[key];
          if (typeof v === "number") return v <= 1 ? v * 100 : v;
          const aliases: Record<string, string[]> = {
            acuracia: ["Acurácia", "acuracia"],
            auc: ["AUC", "auc"],
            recall: ["Recall", "recall"],
            precisao: ["Prec", "Prec.", "precisao"],
            f1: ["F1", "f1"],
            kappa: ["Kappa", "kappa"],
            mcc: ["MCC", "mcc"],
          };
          for (const a of Object.values(aliases)) {
            for (const k of a) {
              const val = row[k];
              if (typeof val === "number") return val <= 1 ? val * 100 : val;
            }
          }
          return 0;
        };
        const sorted = [...modelos_comparados].sort((a, b) => {
          if (!modelsSortBy || modelsSortBy === "modelo" || modelsSortBy === "model" || modelsSortBy === "Model") return 0;
          const va = getNum(a, modelsSortBy);
          const vb = getNum(b, modelsSortBy);
          return modelsSortDesc ? vb - va : va - vb;
        });
        return (
          <div className="rounded-xl border border-white/10 bg-card/50 p-4 shadow-md transition-all duration-200 hover:shadow-lg hover:border-white/15 overflow-x-auto">
            <h4 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-primary" />
              Modelos comparados
            </h4>
            <div className="min-w-[400px]">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    {cols.map((h) => (
                      <th
                        key={h}
                        onClick={() => metricCols.includes(h) && (modelsSortBy === h ? setModelsSortDesc((d) => !d) : (setModelsSortBy(h), setModelsSortDesc(true)))}
                        className={cn(
                          "text-left py-2 px-2 font-medium text-muted-foreground",
                          metricCols.includes(h) && "cursor-pointer hover:text-foreground"
                        )}
                      >
                        {formatMetricKey(h)}
                        {modelsSortBy === h && (modelsSortDesc ? <ChevronDown className="inline h-3 w-3 ml-0.5" /> : <ChevronUp className="inline h-3 w-3 ml-0.5" />)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((row, i) => {
                    const rowModel = String(row.Model ?? row.modelo ?? row.model ?? "").replace(/\s/g, "");
                    const chosenNorm = (modelo_escolhido ?? "").replace(/\s/g, "");
                    const isChosen = chosenNorm && (rowModel.includes(chosenNorm) || chosenNorm.includes(rowModel));
                    return (
                      <tr
                        key={i}
                        className={cn(
                          "border-b border-white/5 hover:bg-white/5",
                          isChosen && "bg-primary/10 border-l-4 border-l-primary"
                        )}
                      >
                        {cols.map((k) => {
                          const v = row[k];
                          const isNum = typeof v === "number";
                          const pct = isNum ? (v <= 1 ? v * 100 : v) : 0;
                          const colorClass = isNum && metricCols.includes(k) ? getMetricColorClass(pct) : "";
                          return (
                            <td key={k} className={cn("py-2 px-2 font-mono tabular-nums", colorClass)}>
                              {isNum ? (v <= 1 ? `${(v * 100).toFixed(1)}%` : v.toFixed(2)) : String(v ?? "—")}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })()}

      {/* Previsões (PulsoAPI: badge resumo, Yes=warning/No=success) */}
      {previsoes_amostra && previsoes_amostra.length > 0 && (() => {
        const total = metricas_negocio?.total_amostra ?? previsoes_amostra.length;
        const dist = metricas_negocio?.distribuicao_classe ?? previsoes_amostra.reduce((acc: Record<string, number>, p) => {
          const k = String(p);
          acc[k] = (acc[k] ?? 0) + 1;
          return acc;
        }, {});
        const yesCount = dist["Yes"] ?? dist["yes"] ?? 0;
        const noCount = dist["No"] ?? dist["no"] ?? total - yesCount;
        return (
          <div className="rounded-xl border border-white/10 bg-card/50 p-4 shadow-md transition-all duration-200 hover:shadow-lg hover:border-white/15">
            <h4 className="text-base font-semibold text-foreground mb-4">Previsões</h4>
            <div className="flex flex-wrap gap-2 mb-3">
              <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-muted/50 text-muted-foreground">
                {total.toLocaleString("pt-BR")} previsões
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-emerald-600/80 text-white">
                {noCount.toLocaleString("pt-BR")} No
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-amber-600/80 text-white">
                {yesCount.toLocaleString("pt-BR")} Yes
              </span>
            </div>
            {/* Tabela amostra (PulsoAPI PredictionsDisplay) */}
            <div className="overflow-x-auto rounded-lg border border-white/10 max-h-[200px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs">#</th>
                    <th className="text-left py-2 px-3 font-medium text-muted-foreground text-xs">Previsão</th>
                  </tr>
                </thead>
                <tbody>
                  {previsoes_amostra.slice(0, 20).map((v, i) => (
                    <tr key={i} className="border-b border-white/5 last:border-0">
                      <td className="py-2 px-3 font-mono text-muted-foreground">{i + 1}</td>
                      <td className="py-2 px-3">
                        <span
                          className={cn(
                            "inline-flex px-2 py-0.5 rounded text-xs font-mono",
                            String(v).toLowerCase() === "yes" || String(v) === "1"
                              ? "bg-amber-600/80 text-white"
                              : "bg-emerald-600/80 text-white"
                          )}
                        >
                          {String(v)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {previsoes_amostra.length > 20 && (
              <p className="text-xs text-muted-foreground mt-2">+{previsoes_amostra.length - 20} previsões</p>
            )}
          </div>
        );
      })()}
    </div>
  );
}
