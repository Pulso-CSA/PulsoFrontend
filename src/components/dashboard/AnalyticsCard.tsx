/**
 * Analytics Card — Padrão oficial de métricas
 * Estilo Post Views: valor principal + timeline/gráfico
 * Ao hover: tooltip glass com insight de exemplo
 */
import { useState } from "react";
import { BarChart3, TrendingUp } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";

export interface AnalyticsCardProps {
  title: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean;
  period?: string;
  data?: Array<{ label: string; value: number }>;
  /** Linhas de insight exibidas no hover (ex.: 5 linhas) */
  insight?: string[];
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
  insight,
  compact = false,
  className,
}: AnalyticsCardProps) {
  const [isHovered, setIsHovered] = useState(false);

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
          <span className="p-2 rounded-full bg-success/20 flex items-center justify-center">
            <BarChart3 className="h-4 w-4 text-success" />
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
      {/* Tooltip glass com insight — aparece ao passar o mouse */}
      {insight && insight.length > 0 && isHovered && (
        <div className="pulso-insight-tooltip absolute inset-0 z-10 flex items-center justify-center p-4 rounded-2xl pointer-events-none">
          <div className="pulso-insight-glass w-full max-w-[90%] p-4 rounded-xl text-left">
            {insight.slice(0, 5).map((line, i) => (
              <p key={i} className="text-xs text-foreground/95 leading-relaxed">
                {line}
              </p>
            ))}
          </div>
        </div>
      )}
      {data.length > 0 && (
        <div className={cn("mt-3 -mx-2", compact ? "h-16" : "h-24")}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="analyticsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground) / 0.5)" />
              <YAxis hide domain={["auto", "auto"]} />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "0.5rem",
                }}
                formatter={(value: number) => [value.toLocaleString("pt-BR"), "views"]}
              />
              <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" fill="url(#analyticsGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
