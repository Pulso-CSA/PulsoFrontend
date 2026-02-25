import { useRef, useState } from "react";
import { Check, AlertTriangle, ChevronLeft, ChevronRight, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
} from "recharts";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

type GraficoMetadado = {
  tipo?: string;
  titulo?: string;
  eixo_x?: string;
  eixo_y?: string;
  explicacao?: string;
  vantagens?: string[];
  desvantagens?: string[];
};

type GraficoDados = {
  labels?: string[];
  values?: number[];
  x?: number[];
  y?: number[];
};

/** Paleta consistente e acessível (indigo, green, amber, pink, teal, violet) */
const CHART_COLORS = [
  "#6366f1", /* indigo */
  "#22c55e", /* green */
  "#f59e0b", /* amber */
  "#ec4899", /* pink */
  "#14b8a6", /* teal */
  "#8b5cf6", /* violet */
];

const MAX_LABEL_LENGTH = 12;

function truncateLabel(label: string): string {
  if (typeof label !== "string") return String(label);
  return label.length > MAX_LABEL_LENGTH ? label.slice(0, 10) + "…" : label;
}

/** Tooltip customizado: "contagem: 242" (sem espaço antes do :) */
function ChartTooltipContent({
  active,
  payload,
  label,
  meta,
}: {
  active?: boolean;
  payload?: Array<{ value?: number; payload?: { x?: number; y?: number } }>;
  label?: string;
  meta: GraficoMetadado;
}) {
  if (!active || !payload?.length) return null;
  const eixoY = (meta.eixo_y ?? "Valor").trim();
  const value = payload[0]?.value ?? payload[0]?.payload?.y;
  const displayLabel = label != null ? String(label) : "";
  return (
    <div className="rounded-lg border border-border/50 bg-card px-3 py-2 text-xs shadow-lg">
      {displayLabel && (
        <p className="font-medium text-foreground mb-1">
          {meta.eixo_x ? `${meta.eixo_x}: ${displayLabel}` : displayLabel}
        </p>
      )}
      <p className="text-muted-foreground">
        <span className="font-medium text-foreground">{eixoY}:</span> {value != null ? Number(value).toLocaleString("pt-BR") : "—"}
      </p>
    </div>
  );
}

interface DataChatChartsProps {
  graficosMetadados?: GraficoMetadado[];
  graficosDados?: GraficoDados[];
}

export function DataChatCharts({ graficosMetadados = [], graficosDados = [] }: DataChatChartsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  if (!graficosMetadados?.length || !graficosDados?.length) return null;

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const scrollLeft = el.scrollLeft;
    const cards = el.querySelectorAll("[data-chart-card]");
    let best = 0;
    let bestDist = Infinity;
    cards.forEach((c, i) => {
      const card = c as HTMLElement;
      const dist = Math.abs(card.offsetLeft - scrollLeft);
      if (dist < bestDist) {
        bestDist = dist;
        best = i;
      }
    });
    setActiveIndex(best);
  };

  const scrollTo = (index: number) => {
    const el = scrollRef.current;
    if (!el) return;
    const card = el.querySelector(`[data-chart-card="${index}"]`) as HTMLElement;
    if (card) {
      el.scrollTo({ left: card.offsetLeft, behavior: "smooth" });
      setActiveIndex(index);
    }
  };

  const cardClass = "rounded-xl border border-white/10 bg-card/50 shadow-md p-4 flex-shrink-0 snap-start flex flex-col min-w-[320px] max-w-[95vw] transition-all duration-200 hover:shadow-lg hover:border-white/15";

  return (
    <div className="mt-6 space-y-4">
      <h3 className="text-lg font-semibold text-foreground mb-4">📊 Gráficos</h3>
      <div className="relative">
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex overflow-x-auto gap-6 pb-4 pr-4 scroll-smooth snap-x snap-mandatory"
          style={{ scrollbarWidth: "thin", scrollBehavior: "smooth" }}
        >
          {graficosMetadados.map((meta, i) => {
            const dados = graficosDados[i];
            if (!dados) return null;

            const tipo = (meta.tipo ?? "barra").toLowerCase();

            if (tipo === "histograma" || tipo === "barra") {
              const labels = dados.labels ?? [];
              const values = dados.values ?? [];
              const chartData = labels.map((l, j) => ({ name: l, value: values[j] ?? 0 }));
              if (chartData.length === 0) return null;

              return (
                <div
                  key={i}
                  data-chart-card={i}
                  className={cardClass}
                >
                <h4 className="text-base font-semibold text-foreground mb-2 break-words whitespace-normal" title={meta.titulo}>
                  {meta.titulo ?? `Gráfico ${i + 1}`}
                </h4>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 13 }}
                      tickFormatter={(v) => truncateLabel(String(v))}
                    />
                    <YAxis tick={{ fontSize: 13 }} />
                    <Tooltip
                      content={({ active, payload, label }) => (
                        <ChartTooltipContent active={active} payload={payload} label={label} meta={meta} />
                      )}
                      cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
                    />
                    <Bar dataKey="value" fill={CHART_COLORS[i % CHART_COLORS.length]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="space-y-2 mt-3">
                  {meta.explicacao && (
                    <p className="text-sm text-muted-foreground leading-relaxed break-words whitespace-normal" title={meta.explicacao}>
                      {meta.explicacao}
                    </p>
                  )}
                  {(meta.vantagens?.length || meta.desvantagens?.length) ? (
                    <Collapsible defaultOpen={false}>
                      <CollapsibleTrigger className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
                        <HelpCircle className="h-3.5 w-3.5" />
                        Vantagens e desvantagens
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        {meta.vantagens?.length ? (
                          <div className="mt-2">
                            <span className="text-sm font-medium text-green-400/90 flex items-center gap-1">
                              <Check className="h-3 w-3" /> Vantagens:
                            </span>
                            <ul className="text-sm text-muted-foreground list-disc list-inside mt-0.5 space-y-0.5">
                              {meta.vantagens.map((v, j) => (
                                <li key={j}>{v}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                        {meta.desvantagens?.length ? (
                          <div className="mt-2">
                            <span className="text-sm font-medium text-amber-400/90 flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3" /> Desvantagens:
                            </span>
                            <ul className="text-sm text-muted-foreground list-disc list-inside mt-0.5 space-y-0.5">
                              {meta.desvantagens.map((d, j) => (
                                <li key={j}>{d}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                      </CollapsibleContent>
                    </Collapsible>
                  ) : null}
                </div>
              </div>
            );
          }

          if (tipo === "dispersao" || tipo === "dispersão") {
            const xArr = dados.x ?? [];
            const yArr = dados.y ?? [];
            const chartData = xArr.map((xv, j) => ({ x: xv, y: yArr[j] ?? 0 }));
            if (chartData.length === 0) return null;

            return (
              <div
                key={i}
                data-chart-card={i}
                className={cardClass}
              >
                <h4 className="text-base font-semibold text-foreground mb-2 break-words whitespace-normal" title={meta.titulo}>
                  {meta.titulo ?? `Dispersão ${i + 1}`}
                </h4>
                <ResponsiveContainer width="100%" height={180}>
                  <ScatterChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                    <XAxis
                      dataKey="x"
                      type="number"
                      name={meta.eixo_x}
                      tick={{ fontSize: 13 }}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      name={meta.eixo_y}
                      tick={{ fontSize: 13 }}
                    />
                    <Tooltip
                      content={({ active, payload }) =>
                        payload?.[0]?.payload ? (
                          <ChartTooltipContent
                            active={active}
                            payload={[{ value: payload[0].payload.y, payload: payload[0].payload }]}
                            label={String(payload[0].payload.x)}
                            meta={meta}
                          />
                        ) : null
                      }
                      cursor={{ strokeDasharray: "3 3" }}
                    />
                    <Scatter data={chartData} fill={CHART_COLORS[i % CHART_COLORS.length]}>
                      {chartData.map((_, idx) => (
                        <Cell key={idx} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
                <div className="space-y-2 mt-3">
                  {meta.explicacao && (
                    <p className="text-sm text-muted-foreground leading-relaxed break-words whitespace-normal" title={meta.explicacao}>
                      {meta.explicacao}
                    </p>
                  )}
                  {(meta.vantagens?.length || meta.desvantagens?.length) ? (
                    <Collapsible defaultOpen={false}>
                      <CollapsibleTrigger className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
                        <HelpCircle className="h-3.5 w-3.5" />
                        Vantagens e desvantagens
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        {meta.vantagens?.length ? (
                          <div className="mt-2">
                            <span className="text-sm font-medium text-green-400/90 flex items-center gap-1">
                              <Check className="h-3 w-3" /> Vantagens:
                            </span>
                            <ul className="text-sm text-muted-foreground list-disc list-inside mt-0.5 space-y-0.5">
                              {meta.vantagens.map((v, j) => (
                                <li key={j}>{v}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                        {meta.desvantagens?.length ? (
                          <div className="mt-2">
                            <span className="text-sm font-medium text-amber-400/90 flex items-center gap-1">
                              <AlertTriangle className="h-3 w-3" /> Desvantagens:
                            </span>
                            <ul className="text-sm text-muted-foreground list-disc list-inside mt-0.5 space-y-0.5">
                              {meta.desvantagens.map((d, j) => (
                                <li key={j}>{d}</li>
                              ))}
                            </ul>
                          </div>
                        ) : null}
                      </CollapsibleContent>
                    </Collapsible>
                  ) : null}
                </div>
              </div>
            );
          }

          return null;
        })}
        </div>

        {/* Indicador de posição e navegação */}
        {graficosMetadados.length > 1 && (
          <div className="flex items-center justify-center gap-4 mt-4">
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9 shrink-0 hover:bg-muted"
              onClick={() => scrollTo(Math.max(0, activeIndex - 1))}
              disabled={activeIndex === 0}
              aria-label="Gráfico anterior"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex gap-2">
              {graficosMetadados.map((_, i) => (
                <button
                  key={i}
                  onClick={() => scrollTo(i)}
                  className={`w-2.5 h-2.5 rounded-full transition-colors ${
                    i === activeIndex ? "bg-primary scale-110" : "bg-muted-foreground/40 hover:bg-muted-foreground/60"
                  }`}
                  aria-label={`Ir para gráfico ${i + 1}`}
                />
              ))}
            </div>
            <span className="text-xs text-muted-foreground tabular-nums min-w-[4rem] whitespace-nowrap">
              Gráfico {activeIndex + 1} de {graficosMetadados.length}
            </span>
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9 shrink-0 hover:bg-muted"
              onClick={() => scrollTo(Math.min(graficosMetadados.length - 1, activeIndex + 1))}
              disabled={activeIndex === graficosMetadados.length - 1}
              aria-label="Próximo gráfico"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
