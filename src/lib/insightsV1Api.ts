/**
 * Cliente para Insights v1 (/insights/v1/*) — NL → gráfico/KPI, sessões e artefatos.
 * Catálogo é público; demais rotas usam Bearer (apiRequest).
 */
import { apiRequest } from "./api";
import type { AnalyticsChartType } from "@/components/dashboard/AnalyticsCard";
import type { InsightsServiceFilter, InsightsWidgetResponse } from "./api";

export type InsightsV1WidgetPayload = InsightsWidgetResponse & {
  backendInsightId?: string;
  backendSessionId?: string;
};

const V1 = "/insights/v1";

/* ---------- Tipos (alinhados ao backend; campos opcionais para evolução) ---------- */

export type InsightV1Status = string;

export type InsightV1DataPoint = {
  label?: string;
  x?: string;
  y?: number;
  value?: number;
  name?: string;
};

export type InsightV1Series = {
  name?: string;
  label?: string;
  points?: InsightV1DataPoint[];
  data?: InsightV1DataPoint[];
  values?: number[];
};

export type InsightV1Kpi = {
  value?: number | string;
  display_value?: string;
  unit?: string;
  change_pct?: number;
  trend?: string;
  target?: number;
  current?: number;
};

export type InsightV1Ambiguity = {
  message?: string;
  suggestions?: string[];
  options?: Array<Record<string, unknown>>;
  prompts?: string[];
  [key: string]: unknown;
};

export type InsightQueryRequest = {
  prompt: string;
  session_id?: string | null;
  id_requisicao?: string | null;
  locale?: string | null;
};

export type InsightQueryResponse = {
  insight_id?: string;
  session_id?: string;
  status?: InsightV1Status;
  chart_type?: string;
  title?: string;
  description?: string;
  labels?: string[];
  series?: InsightV1Series[];
  kpi?: InsightV1Kpi;
  aggregated_metrics?: Record<string, number | string>;
  filters_applied?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  ambiguity?: InsightV1Ambiguity | null;
};

export type CatalogResponse = {
  chart_types?: Array<{ id?: string; label?: string; description?: string }>;
  services?: unknown[];
  capabilities?: unknown[];
  example_prompts?: string[];
  version?: string;
};

export type InsightSessionCreateBody = { title?: string | null };

export type InsightSessionCreateResponse = {
  session_id: string;
  created_at?: string;
};

export type InsightSessionDetail = {
  session_id?: string;
  id?: string;
  title?: string;
  updated_at?: string;
  created_at?: string;
  [key: string]: unknown;
};

export const insightsV1Api = {
  getCatalog: () =>
    apiRequest<CatalogResponse>(`${V1}/catalog`, { skipAuth: true, method: "GET" }),

  query: (body: InsightQueryRequest) =>
    apiRequest<InsightQueryResponse>(`${V1}/query`, {
      method: "POST",
      body: JSON.stringify({
        prompt: body.prompt,
        session_id: body.session_id ?? undefined,
        id_requisicao: body.id_requisicao ?? undefined,
        locale: body.locale ?? undefined,
      }),
    }),

  createSession: (body?: InsightSessionCreateBody) =>
    apiRequest<InsightSessionCreateResponse>(`${V1}/sessions`, {
      method: "POST",
      body: JSON.stringify(body ?? {}),
    }),

  listSessions: (limit?: number) => {
    const q = limit != null ? `?limit=${encodeURIComponent(String(limit))}` : "";
    return apiRequest<InsightSessionDetail[]>(`${V1}/sessions${q}`, { method: "GET" });
  },

  getSession: (sessionId: string) =>
    apiRequest<Record<string, unknown>>(`${V1}/sessions/${encodeURIComponent(sessionId)}`, {
      method: "GET",
    }),

  getPrompts: (sessionId: string, limit?: number) => {
    const q = limit != null ? `?limit=${encodeURIComponent(String(limit))}` : "";
    return apiRequest<Record<string, unknown>[]>(
      `${V1}/sessions/${encodeURIComponent(sessionId)}/prompts${q}`,
      { method: "GET" }
    );
  },

  getArtifacts: (sessionId: string, limit?: number) => {
    const q = limit != null ? `?limit=${encodeURIComponent(String(limit))}` : "";
    return apiRequest<Record<string, unknown>[]>(
      `${V1}/sessions/${encodeURIComponent(sessionId)}/artifacts${q}`,
      { method: "GET" }
    );
  },
};

/** Mapeia chart_type do backend para AnalyticsCard. */
export function mapV1ChartType(chartType: string | undefined): AnalyticsChartType {
  const t = (chartType ?? "area").toLowerCase().replace(/-/g, "_");
  if (t === "kpi_card" || t === "kpi" || t === "metric") return "progress";
  if (t === "bar" || t === "column") return "bar";
  if (t === "line") return "line";
  if (t === "pie" || t === "donut") return "pie";
  if (t === "progress" || t === "gauge") return "progress";
  if (t === "area") return "area";
  return "area";
}

function pickSeriesPoints(s: InsightV1Series): InsightV1DataPoint[] {
  if (Array.isArray(s.points) && s.points.length) return s.points;
  if (Array.isArray(s.data) && s.data.length) return s.data;
  return [];
}

/** Converte series + labels em dados do Recharts. */
export function v1SeriesToChartData(
  series: InsightV1Series[] | undefined,
  labels: string[] | undefined
): Array<{ label: string; value: number }> {
  if (!series?.length) {
    if (labels?.length) {
      return labels.map((label, i) => ({ label, value: 0 }));
    }
    return [];
  }

  const first = series[0];
  const pts = pickSeriesPoints(first);
  if (pts.length) {
    return pts.map((p, i) => ({
      label: p.label ?? p.x ?? p.name ?? labels?.[i] ?? `P${i + 1}`,
      value: typeof p.value === "number" ? p.value : typeof p.y === "number" ? p.y : 0,
    }));
  }

  if (Array.isArray(first.values) && first.values.length) {
    const labs = labels?.length === first.values.length ? labels : first.values.map((_, i) => `S${i + 1}`);
    return first.values.map((value, i) => ({ label: labs[i] ?? `S${i + 1}`, value }));
  }

  if (labels?.length && series.length > 1) {
    return labels.map((label, i) => {
      const s = series[i];
      const v = s?.values?.[0] ?? pickSeriesPoints(s)[0]?.value ?? pickSeriesPoints(s)[0]?.y ?? 0;
      return { label, value: typeof v === "number" ? v : Number(v) || 0 };
    });
  }

  return [];
}

function formatAggregated(m: Record<string, number | string> | undefined): string | undefined {
  if (!m || typeof m !== "object") return undefined;
  const entries = Object.entries(m);
  if (!entries.length) return undefined;
  const [k, v] = entries[0];
  return `${k}: ${typeof v === "number" ? v.toLocaleString("pt-BR") : String(v)}`;
}

function inferServiceFromMetadata(meta: Record<string, unknown> | undefined): InsightsServiceFilter {
  const raw =
    (meta?.service as string) ||
    (meta?.services as string[])?.[0] ||
    (meta?.service_filter as string) ||
    "";
  const s = raw.toLowerCase();
  if (s.includes("pulso") || s === "pulso") return "pulso";
  if (s.includes("cloud") || s === "cloud") return "cloud";
  if (s.includes("finops") || s.includes("fin")) return "finops";
  if (s.includes("custom")) return "custom";
  return "data";
}

/**
 * Constrói payload compatível com InsightsWidgetResponse + ids do backend.
 */
export function mapInsightV1ResponseToWidget(
  res: InsightQueryResponse,
  opts?: { widgetId?: string; customPrompt?: string }
): InsightsV1WidgetPayload {
  const chartType = mapV1ChartType(res.chart_type);
  const data = v1SeriesToChartData(res.series, res.labels);

  const kpi = res.kpi;
  let valueStr =
    kpi?.display_value ??
    (kpi?.value != null ? String(kpi.value) : undefined) ??
    formatAggregated(res.aggregated_metrics);

  if (!valueStr && data.length) {
    const sum = data.reduce((a, d) => a + d.value, 0);
    valueStr = sum.toLocaleString("pt-BR");
  }
  if (!valueStr) valueStr = "—";

  const trend = kpi?.trend ?? (kpi?.change_pct != null ? `${kpi.change_pct > 0 ? "+" : ""}${kpi.change_pct}%` : "—");

  const title = (res.title?.trim() || res.description?.slice(0, 48) || "Insight").trim();
  const description = res.description ?? "";

  const insights: string[] = [];
  if (description) insights.push(description);
  if (res.status && res.status !== "ok" && res.status !== "success") {
    insights.push(`Estado: ${res.status}`);
  }
  if (res.ambiguity) {
    const amb = res.ambiguity;
    if (amb.message) insights.push(String(amb.message));
    const sug = amb.suggestions ?? amb.prompts ?? [];
    sug.forEach((s) => insights.push(typeof s === "string" ? s : JSON.stringify(s)));
  }
  if (res.filters_applied && Object.keys(res.filters_applied).length) {
    insights.push(`Filtros: ${JSON.stringify(res.filters_applied)}`);
  }

  let progressPercent: number | undefined;
  if (chartType === "progress" && kpi) {
    const tgt = kpi.target;
    const cur = kpi.current ?? (typeof kpi.value === "number" ? kpi.value : undefined);
    if (typeof tgt === "number" && tgt > 0 && typeof cur === "number") {
      progressPercent = Math.min(100, Math.round((cur / tgt) * 100));
    } else if (typeof kpi.value === "number" && kpi.value <= 100 && kpi.value >= 0) {
      progressPercent = Math.round(kpi.value);
    }
  }

  const meta = res.metadata ?? {};
  const serviceFilter = inferServiceFromMetadata(meta);

  const widget: InsightsV1WidgetPayload = {
    id: opts?.widgetId ?? res.insight_id ?? `v1-${Date.now()}`,
    title,
    value: valueStr,
    trend,
    period: (meta.period as string) || (meta.time_range as string) || "Insights v1",
    chart_type: chartType,
    progress_percent: progressPercent,
    insights: insights.length ? insights : ["Sem texto adicional."],
    service_filter: serviceFilter,
    custom_prompt: opts?.customPrompt,
    analysis_summary: description || title,
    technical_conclusion:
      (meta.technical_conclusion as string) ||
      (res.status === "degraded" ? "Resposta degradada; refine o prompt ou escolha uma sugestão." : undefined) ||
      undefined,
    data: data.length ? data : undefined,
    backendInsightId: res.insight_id,
    backendSessionId: res.session_id,
  };

  return widget;
}

/** Artefatos Mongo podem ser o payload completo ou aninhado. */
export function artifactRecordToQueryResponse(row: Record<string, unknown>): InsightQueryResponse | null {
  const nested = (row.payload ??
    row.chart_payload ??
    row.insight_payload ??
    row.response ??
    row.insight) as Record<string, unknown> | undefined;
  const payload = (nested && typeof nested === "object" ? nested : row) as Record<string, unknown>;
  if (!payload || typeof payload !== "object") return null;
  if (payload.chart_type != null || payload.title != null || payload.series != null || payload.status != null) {
    return payload as unknown as InsightQueryResponse;
  }
  return null;
}
