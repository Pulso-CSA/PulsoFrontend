/**
 * Analytics Card — Padrão oficial de métricas
 * Estilo Post Views: valor principal + timeline/gráfico
 * Ao hover: tooltip glass com insight de exemplo
 */
import { useState } from "react";
import { BarChart3, TrendingUp, DollarSign } from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { cn } from "@/lib/utils";

export type AnalyticsChartType = "area" | "bar" | "line" | "pie" | "progress";

export interface AnalyticsCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean;
  period?: string;
  data?: Array<{ label: string; value: number }>;
  /** Tipo de gráfico: area (padrão), bar (elemento 14), progress (elemento 16) */
  chartType?: AnalyticsChartType;
  /** Progresso 0-100 para chartType="progress" (elemento 16 Sales) */
  progressPercent?: number;
  /** Linhas de insight exibidas no hover (ex.: 5 linhas) */
  insight?: string[];
  /** Resumo breve: o que o gráfico analisa (hover) */
  analysisSummary?: string;
  /** Conclusão técnica (hover) */
  technicalConclusion?: string;
  /** Modo compacto para tela de insights (gráfico menor) */
  compact?: boolean;
  className?: string;
}

const defaultData = [
  { label: "8am", value: 120 },
  { label: "10am", value: 280 },
  { label: "12pm", value: 450 },
  { label: "2pm", value: 380 },
  { label: "4pm", value: 520 },
  { label: "6pm", value: 412 },
];

export function AnalyticsCard({
  title,
  value,
  trend,
  trendUp = true,
  period = "Últimas 24h",
  data = defaultData,
  chartType = "area",
  progressPercent = 76,
  insight,
  analysisSummary,
  technicalConclusion,
  compact = false,
  className,
}: AnalyticsCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const isProgress = chartType === "progress";
  const isBar = chartType === "bar";
  const isLine = chartType === "line";
  const isPie = chartType === "pie";

  const PIE_COLORS = ["hsl(var(--primary))", "hsl(var(--primary) / 0.85)", "hsl(var(--primary) / 0.7)", "hsl(var(--primary) / 0.55)", "hsl(var(--primary) / 0.4)"];

  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-card/60 backdrop-blur-xl p-5 overflow-visible relative",
        "shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1),0_4px_6px_-2px_rgba(0,0,0,0.05)]",
        "transition-transform duration-200",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={cn(
            "p-2 rounded-full flex items-center justify-center",
            isProgress ? "bg-success/20" : "bg-success/20"
          )}>
            {isProgress ? (
              <DollarSign className="h-4 w-4 text-success" />
            ) : (
              <BarChart3 className="h-4 w-4 text-success" />
            )}
          </span>
          <span className="text-sm font-medium text-foreground">{title}</span>
        </div>
        {trend && (
          <span
            className={cn(
              "text-xs font-semibold flex items-center gap-0.5",
              trendUp ? "text-success" : "text-destructive"
            )}
          >
            <TrendingUp className={cn("h-3 w-3", !trendUp && "rotate-180")} />
            {trend}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-foreground tabular-nums">{value}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{period}</p>
      {/* Tooltip glass: análise breve + conclusão técnica + insights — aparece ao passar o mouse */}
      {(insight?.length || analysisSummary || technicalConclusion) && isHovered && (
        <div className="pulso-insight-tooltip absolute inset-0 z-10 flex items-center justify-center p-4 rounded-2xl pointer-events-none">
          <div className="pulso-insight-glass w-full max-w-[90%] p-4 rounded-xl text-left space-y-2">
            {analysisSummary && (
              <p className="text-xs font-medium text-foreground/95">{analysisSummary}</p>
            )}
            {technicalConclusion && (
              <p className="text-xs text-primary/90 border-l-2 border-primary/50 pl-2">{technicalConclusion}</p>
            )}
            {insight && insight.length > 0 && insight.slice(0, 5).map((line, i) => (
              <p key={i} className="text-xs text-foreground/95 leading-relaxed">
                {line}
              </p>
            ))}
          </div>
        </div>
      )}
      {isProgress ? (
        <div className="mt-3">
          <div className="h-2 rounded-full bg-muted/50 overflow-hidden">
            <div
              className="h-full rounded-full bg-success transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
            />
          </div>
        </div>
      ) : data.length > 0 && (
        <div className={cn("mt-3 -mx-2", compact ? "h-[140px]" : "h-[180px]")}>
          <ResponsiveContainer width="100%" height="100%">
            {isPie ? (
              <PieChart margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                    fontSize: "12px",
                  }}
                  formatter={(value: number, name: string) => [value.toLocaleString("pt-BR"), name]}
                />
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={compact ? 28 : 36}
                  outerRadius={compact ? 42 : 52}
                  paddingAngle={2}
                  onMouseEnter={(_, index) => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(null)}
                >
                  {data.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} stroke="transparent" strokeWidth={activeIndex === index ? 2 : 0} />
                  ))}
                </Pie>
              </PieChart>
            ) : isLine ? (
              <LineChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border) / 0.5)" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground) / 0.6)" />
                <YAxis hide domain={["auto", "auto"]} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                  }}
                  formatter={(value: number) => [value.toLocaleString("pt-BR"), "valor"]}
                  cursor={{ stroke: "hsl(var(--primary) / 0.5)", strokeWidth: 1 }}
                />
                <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ fill: "hsl(var(--primary))", strokeWidth: 0 }} activeDot={{ r: 4, strokeWidth: 2 }} />
              </LineChart>
            ) : isBar ? (
              <BarChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border) / 0.5)" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground) / 0.6)" />
                <YAxis hide domain={["auto", "auto"]} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                  }}
                  formatter={(value: number) => [value.toLocaleString("pt-BR"), "valor"]}
                  cursor={{ fill: "hsl(var(--muted) / 0.3)" }}
                />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : (
              <AreaChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
                <defs>
                  <linearGradient id="analyticsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border) / 0.5)" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground) / 0.6)" />
                <YAxis hide domain={["auto", "auto"]} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "0.5rem",
                  }}
                  formatter={(value: number) => [value.toLocaleString("pt-BR"), "valor"]}
                  cursor={{ stroke: "hsl(var(--primary) / 0.5)", strokeWidth: 1 }}
                />
                <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" fill="url(#analyticsGradient)" strokeWidth={2} />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
