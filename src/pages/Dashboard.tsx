import { useState, useEffect, useLayoutEffect, useRef, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { Monitor, Terminal, RefreshCw, Download, Workflow, CloudCog, TrendingDown, Brain, SlidersHorizontal, LayoutGrid, Plus, Trash2, Link2, Play, Loader2, Activity, BarChart3, TrendingUp, Circle, Percent, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { LayoutA } from "@/layouts/LayoutA";
import type { ServiceKey } from "@/layouts/LayoutA";
import { ShortcutsModal } from "@/components/dashboard/ShortcutsModal";
import PromptPanel from "@/components/dashboard/PromptPanel";
import LogsPanel from "@/components/dashboard/LogsPanel";
import FinOpsChat from "@/components/dashboard/FinOpsChat";
import DataChat from "@/components/dashboard/DataChat";
import CloudChat from "@/components/dashboard/CloudChat";
import { AnalyticsCard } from "@/components/dashboard/AnalyticsCard";
import { InsightsFab } from "@/components/dashboard/InsightsFab";
import { InsightsChatBar } from "@/components/dashboard/InsightsChatBar";
import { Slider } from "@/components/ui/slider";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import type { AnalyticsChartType } from "@/components/dashboard/AnalyticsCard";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { previewApi, type InsightsWidgetResponse } from "@/lib/api";
import {
  insightsV1Api,
  mapInsightV1ResponseToWidget,
  artifactRecordToQueryResponse,
  type InsightQueryResponse,
  type InsightSessionDetail,
} from "@/lib/insightsV1Api";
import { emitPulsoNotification } from "@/lib/pulsoNotifications";

export type InsightsFilterKey = "all" | ServiceKey | "custom";

type InsightsWidget = {
  id: string;
  title: string;
  value: string;
  trend: string;
  period: string;
  chartType: AnalyticsChartType;
  progressPercent?: number;
  insights: string[];
  /** Filtro de serviço ao qual o gráfico pertence (para navbar) */
  serviceFilter?: ServiceKey | "custom";
  /** Prompt em linguagem natural usado na customização */
  customPrompt?: string;
  /** Resumo breve: o que o gráfico analisa (hover) */
  analysisSummary?: string;
  /** Conclusão técnica (hover) */
  technicalConclusion?: string;
  /** Dados customizados para o gráfico (opcional) */
  data?: Array<{ label: string; value: number }>;
  backendInsightId?: string;
  backendSessionId?: string;
};

type InsightsChatHistoryItem = {
  id: string;
  prompt: string;
  createdAt: number;
  status: "gerando" | "criado" | "fallback" | "orientacao";
  chartTitle?: string;
  assistantMessage?: string;
};

const INSIGHTS_V1_SESSION_STORAGE_KEY = "pulso_insights_v1_session_id";

const buildInsightsRequestId = () =>
  (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
    ? crypto.randomUUID()
    : `ins-${Date.now()}`;

function unwrapInsightSessionList(raw: unknown): InsightSessionDetail[] {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object" && "sessions" in raw && Array.isArray((raw as { sessions: unknown }).sessions)) {
    return (raw as { sessions: InsightSessionDetail[] }).sessions;
  }
  return [];
}

const mapApiWidgetToDashboard = (widget: InsightsWidgetResponse): InsightsWidget => {
  const ext = widget as InsightsWidgetResponse & {
    backendInsightId?: string;
    backendSessionId?: string;
  };
  return {
    id: widget.id,
    title: widget.title,
    value: widget.value,
    trend: widget.trend,
    period: widget.period,
    chartType: widget.chart_type,
    progressPercent: widget.progress_percent,
    insights: widget.insights ?? [],
    serviceFilter: widget.service_filter ?? "data",
    customPrompt: widget.custom_prompt,
    analysisSummary: widget.analysis_summary,
    technicalConclusion: widget.technical_conclusion,
    data: widget.data,
    backendInsightId: ext.backendInsightId,
    backendSessionId: ext.backendSessionId,
  };
};

const isGenericCreateChartPrompt = (prompt: string) => {
  const p = prompt.trim().toLowerCase();
  if (!p) return true;
  return /^(criar|gere|gerar|montar|fazer)?\s*(um\s*)?(gr[aá]fico|grafico|insight)(\s*por\s*chat)?[.!?]*$/.test(p);
};

const Dashboard = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const { t, i18n } = useTranslation();
  const insightsApiLocale = useMemo(
    () => (i18n.language?.toLowerCase().replace(/_/g, "-").startsWith("pt") ? "pt-BR" : "en"),
    [i18n.language]
  );
  const insightsServiceLabels = useMemo(
    () =>
      ({
        pulso: t("dashboard.services.pulso"),
        cloud: t("dashboard.services.cloud"),
        finops: t("dashboard.services.finops"),
        data: t("dashboard.services.data"),
        custom: t("dashboard.services.custom"),
      }) satisfies Record<ServiceKey | "custom", string>,
    [t, i18n.language]
  );
  const insightsChartLabels = useMemo(
    () =>
      ({
        area: t("dashboard.chartTypes.area"),
        bar: t("dashboard.chartTypes.bar"),
        line: t("dashboard.chartTypes.line"),
        pie: t("dashboard.chartTypes.pie"),
        progress: t("dashboard.chartTypes.progress"),
      }) satisfies Record<AnalyticsChartType, string>,
    [t, i18n.language]
  );
  const insightsChartTypeOptions = useMemo(
    () =>
      [
        { type: "area" as const, label: t("dashboard.chartTypes.areaFull"), icon: Activity },
        { type: "bar" as const, label: t("dashboard.chartTypes.barFull"), icon: BarChart3 },
        { type: "line" as const, label: t("dashboard.chartTypes.lineFull"), icon: TrendingUp },
        { type: "pie" as const, label: t("dashboard.chartTypes.pieFull"), icon: Circle },
        { type: "progress" as const, label: t("dashboard.chartTypes.progressFull"), icon: Percent },
      ] as const,
    [t, i18n.language]
  );
  const insightsFilterButtons = useMemo(
    () =>
      [
        { key: "all" as const, icon: LayoutGrid, label: t("dashboard.filterAll") },
        { key: "pulso" as const, icon: Workflow, label: t("dashboard.services.pulso") },
        { key: "cloud" as const, icon: CloudCog, label: t("dashboard.services.cloud") },
        { key: "finops" as const, icon: TrendingDown, label: t("dashboard.services.finops") },
        { key: "data" as const, icon: Brain, label: t("dashboard.services.data") },
        { key: "custom" as const, icon: SlidersHorizontal, label: t("dashboard.services.custom") },
      ] as const,
    [t, i18n.language]
  );
  const [activeService, setActiveService] = useState<ServiceKey | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [previewFrontendUrl, setPreviewFrontendUrlState] = useState<string | null>(
    () => localStorage.getItem("pulso_preview_frontend_url")
  );
  const [rootPathForPreview, setRootPathForPreview] = useState<string | null>(null);
  const [previewStartLoading, setPreviewStartLoading] = useState(false);

  const [insightsWidgets, setInsightsWidgets] = useState<InsightsWidget[]>(() => []);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsGenerating, setInsightsGenerating] = useState(false);
  const [insightsZoom, setInsightsZoom] = useState(1);
  const insightsLayoutMode = "free" as const;
  const [insightsPositions, setInsightsPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [insightsDragging, setInsightsDragging] = useState<{ id: string; startX: number; startY: number; posX: number; posY: number } | null>(null);
  const [insightsMenuOpen, setInsightsMenuOpen] = useState(false);
  const [insightsChatOpen, setInsightsChatOpen] = useState(false);
  const [insightsChatHistory, setInsightsChatHistory] = useState<InsightsChatHistoryItem[]>([]);
  const [insightsFilter, setInsightsFilter] = useState<InsightsFilterKey>("all");
  const [insightsPan, setInsightsPan] = useState({ x: 0, y: 0 });
  const [insightsPanning, setInsightsPanning] = useState<{ startX: number; startY: number; startPanX: number; startPanY: number } | null>(null);
  const [insightsConnections, setInsightsConnections] = useState<{ id: string; from: string; to: string; summary?: string }[]>([]);
  const [insightsV1SessionId, setInsightsV1SessionId] = useState<string | null>(() => {
    try {
      return localStorage.getItem(INSIGHTS_V1_SESSION_STORAGE_KEY);
    } catch {
      return null;
    }
  });
  const [insightsCatalogSuggestions, setInsightsCatalogSuggestions] = useState<string[]>([]);
  const [connectionHoverId, setConnectionHoverId] = useState<string | null>(null);
  /** Aba de gráfico ativa (lista horizontal acima do canvas Insights) */
  const [insightsActiveChartTab, setInsightsActiveChartTab] = useState<string | null>(null);
  const [customizeWidgetId, setCustomizeWidgetId] = useState<string | null>(null);
  const [customizeForm, setCustomizeForm] = useState<{ service: ServiceKey | "custom"; prompt: string }>({ service: "data", prompt: "" });
  const INSIGHTS_ZOOM_MIN = 0.5;
  const INSIGHTS_ZOOM_MAX = 2;
  const insightsZoomContainerRef = useRef<HTMLDivElement>(null);
  const insightsFilterDockRef = useRef<HTMLDivElement>(null);
  const [insightsFilterDockHeight, setInsightsFilterDockHeight] = useState(0);

  useLayoutEffect(() => {
    if (activeService !== null) {
      setInsightsFilterDockHeight(0);
      return;
    }
    const el = insightsFilterDockRef.current;
    if (!el) return;
    const measure = () => setInsightsFilterDockHeight(el.getBoundingClientRect().height);
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [activeService, insightsFilter]);
  const handleInsightsWheel = useCallback((e: WheelEvent) => {
    const el = insightsZoomContainerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const step = 0.08;
    setInsightsZoom((z) => {
      const next = e.deltaY < 0 ? Math.min(INSIGHTS_ZOOM_MAX, z + step) : Math.max(INSIGHTS_ZOOM_MIN, z - step);
      setInsightsPan((p) => ({
        x: p.x + mouseX * (1 - next / z),
        y: p.y + mouseY * (1 - next / z),
      }));
      return next;
    });
    e.preventDefault();
  }, []);
  useEffect(() => {
    const el = insightsZoomContainerRef.current;
    if (!el) return;
    el.addEventListener("wheel", handleInsightsWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleInsightsWheel);
  }, [handleInsightsWheel, activeService]);

  const setPreviewFrontendUrl = (url: string | null) => {
    setPreviewFrontendUrlState(url);
    if (url) localStorage.setItem("pulso_preview_frontend_url", url);
    else localStorage.removeItem("pulso_preview_frontend_url");
  };

  const handleTestarPreview = async () => {
    const rp = rootPathForPreview?.trim();
    if (!rp) {
      toast({
        title: t("dashboard.pathRequiredTitle"),
        description: t("dashboard.pathRequiredDesc"),
        variant: "destructive",
      });
      return;
    }
    setPreviewStartLoading(true);
    try {
      const res = await previewApi.start({ root_path: rp, project_type: "auto" });
      if (res.success) {
        const previewUrl = res.preview_url ?? res.preview_frontend_url ?? null;
        if (previewUrl) {
          setPreviewFrontendUrl(previewUrl);
          setShowPreview(true);
        }
        const msg = res.message ?? t("dashboard.previewStartedDefault");
        toast({
          title: t("dashboard.previewStarted"),
          description: (
            <>
              {msg}
              {previewUrl && (
                <>
                  {" "}
                  <a href={previewUrl} target="_blank" rel="noopener noreferrer" className="text-primary underline font-medium hover:underline">
                    {t("dashboard.openPreviewLink")}
                  </a>
                </>
              )}
            </>
          ),
        });
        if (res.preview_auto_open === true && previewUrl) {
          window.open(previewUrl, "_blank", "noopener,noreferrer");
        }
      } else {
        toast({
          title: t("dashboard.previewError"),
          description: res.message ?? (res.details != null ? String(res.details) : t("dashboard.tryAgainShort")),
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: t("dashboard.previewError"),
        description: err instanceof Error ? err.message : t("dashboard.backendConnectFail"),
        variant: "destructive",
      });
    } finally {
      setPreviewStartLoading(false);
    }
  };

  useEffect(() => {
    const checkout = searchParams.get("checkout");
    if (checkout === "success") {
      toast({
        title: t("dashboard.checkoutSuccess"),
        description: t("dashboard.checkoutSuccessDesc"),
      });
      setSearchParams({}, { replace: true });
    } else if (checkout === "cancel") {
      toast({
        title: t("dashboard.checkoutCancel"),
        description: t("dashboard.checkoutCancelDesc"),
        variant: "destructive",
      });
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, toast, t]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.key === "?") {
        e.preventDefault();
        setShowShortcuts((prev) => !prev);
        return;
      }
      if (e.altKey && e.key === "p") {
        e.preventDefault();
        requestAnimationFrame(() => document.getElementById("prompt-input")?.focus());
      }
      if (e.altKey && e.key === "f") {
        e.preventDefault();
        requestAnimationFrame(() => document.getElementById("finops-input")?.focus());
      }
      if (e.altKey && e.key === "d") {
        e.preventDefault();
        requestAnimationFrame(() => document.getElementById("data-input")?.focus());
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const persistInsightsV1Session = useCallback((sid: string | undefined) => {
    if (!sid) return;
    setInsightsV1SessionId(sid);
    try {
      localStorage.setItem(INSIGHTS_V1_SESSION_STORAGE_KEY, sid);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadInsightsFromV1 = async () => {
      setInsightsLoading(true);
      try {
        const catalog = await insightsV1Api.getCatalog();
        if (!cancelled && catalog.example_prompts?.length) {
          setInsightsCatalogSuggestions(catalog.example_prompts);
        }

        let sessionId: string | undefined;
        try {
          sessionId = localStorage.getItem(INSIGHTS_V1_SESSION_STORAGE_KEY) ?? undefined;
        } catch {
          sessionId = undefined;
        }

        if (!sessionId) {
          try {
            const rawSessions = await insightsV1Api.listSessions(5);
            const list = unwrapInsightSessionList(rawSessions);
            const first = list[0];
            const sid = first?.session_id ?? (typeof first?.id === "string" ? first.id : undefined);
            if (typeof sid === "string") sessionId = sid;
          } catch {
            /* sem sessões ou não autenticado */
          }
        }

        if (!sessionId) {
          if (!cancelled) setInsightsWidgets([]);
          return;
        }

        const artifacts = await insightsV1Api.getArtifacts(sessionId, 50);
        if (cancelled) return;

        const rows = Array.isArray(artifacts) ? artifacts : [];
        const parsed = rows
          .map((row) => artifactRecordToQueryResponse(row as Record<string, unknown>))
          .filter((p): p is InsightQueryResponse => p != null);

        persistInsightsV1Session(sessionId);

        if (!parsed.length) {
          if (!cancelled) setInsightsWidgets([]);
          return;
        }

        const widgets = parsed.map((res, i) => {
          const wid = res.insight_id ?? `v1-loaded-${i}-${Date.now()}`;
          const payload = mapInsightV1ResponseToWidget(res, { widgetId: wid });
          return mapApiWidgetToDashboard(payload);
        });

        if (!cancelled) {
          setInsightsWidgets(widgets);
          setInsightsPositions((pos) => {
            const next = { ...pos };
            widgets.forEach((w, i) => {
              if (!next[w.id]) next[w.id] = { x: 20 + (i % 3) * 280, y: 20 + Math.floor(i / 3) * 200 };
            });
            return next;
          });
        }
      } catch (err) {
        if (!cancelled) {
          toast({
            title: t("dashboard.insightsV1"),
            description: err instanceof Error ? err.message : t("dashboard.insightsV1SyncFail"),
          });
          setInsightsWidgets([]);
        }
      } finally {
        if (!cancelled) setInsightsLoading(false);
      }
    };

    void loadInsightsFromV1();
    return () => {
      cancelled = true;
    };
  }, [toast, persistInsightsV1Session, t]);

  const ZOOM_MIN = 0.5;
  const ZOOM_MAX = 2;
  const ZOOM_STEP = 0.1;

  const handleInsightsZoomIn = () => setInsightsZoom((z) => Math.min(ZOOM_MAX, z + ZOOM_STEP));
  const handleInsightsZoomOut = () => setInsightsZoom((z) => Math.max(ZOOM_MIN, z - ZOOM_STEP));
  const handleInsightsCreateChart = (chartType: AnalyticsChartType = "area") => {
    const sampleDataByType: Record<"area" | "bar" | "line" | "pie", Array<{ label: string; value: number }>> = {
      area: [
        { label: "8h", value: 120 },
        { label: "10h", value: 280 },
        { label: "12h", value: 450 },
        { label: "14h", value: 380 },
        { label: "16h", value: 520 },
        { label: "18h", value: 412 },
      ],
      bar: [
        { label: "Norte", value: 420 },
        { label: "Sul", value: 380 },
        { label: "Leste", value: 510 },
        { label: "Oeste", value: 290 },
        { label: "Centro", value: 340 },
      ],
      line: [
        { label: "Jan", value: 120 },
        { label: "Fev", value: 180 },
        { label: "Mar", value: 145 },
        { label: "Abr", value: 220 },
        { label: "Mai", value: 190 },
        { label: "Jun", value: 260 },
      ],
      pie: [
        { label: "Canal A", value: 35 },
        { label: "Canal B", value: 28 },
        { label: "Canal C", value: 22 },
        { label: "Outros", value: 15 },
      ],
    };
    const isProgressChart = chartType === "progress";
    const chartData = !isProgressChart
      ? sampleDataByType[chartType as "area" | "bar" | "line" | "pie"]
      : [];
    const numLocale = i18n.language?.replace(/_/g, "-") || "pt-BR";
    const value = isProgressChart
      ? "65%"
      : String(chartData.reduce((acc, item) => acc + item.value, 0).toLocaleString(numLocale));

    const id = `widget-${Date.now()}`;
    const newIndex = insightsWidgets.length;
    const defaultService: ServiceKey | "custom" = insightsFilter === "custom" ? "custom" : insightsFilter === "all" ? "data" : insightsFilter;
    setInsightsWidgets((prev) => [
      ...prev,
      {
        id,
        title: t("dashboard.newChartTitle", { type: insightsChartLabels[chartType] }),
        value,
        trend: "+0%",
        period: t("dashboard.periodNow"),
        chartType,
        progressPercent: isProgressChart ? 65 : undefined,
        insights: [],
        serviceFilter: defaultService,
        data: isProgressChart ? undefined : chartData,
      },
    ]);
    if (insightsLayoutMode === "free") {
      setInsightsPositions((pos) => ({ ...pos, [id]: { x: 20 + (newIndex % 3) * 280, y: 20 + Math.floor(newIndex / 3) * 200 } }));
    }
    toast({
      title: t("dashboard.chartCreated"),
      description: t("dashboard.chartCreatedDesc", { type: insightsChartLabels[chartType] }),
    });
  };
  const handleInsightsDeleteChart = (id: string) => {
    setInsightsWidgets((prev) => prev.filter((w) => w.id !== id));
    setInsightsPositions((pos) => {
      const next = { ...pos };
      delete next[id];
      return next;
    });
    setInsightsConnections((prev) => prev.filter((c) => c.from !== id && c.to !== id));
    toast({ title: t("dashboard.chartDeleted"), variant: "destructive" });
  };
  const handleInsightsUpdateChart = async () => {
    const widgetsToRefresh = insightsWidgets.filter((w) => !!w.customPrompt?.trim());
    if (!widgetsToRefresh.length) {
      toast({
        title: t("dashboard.noChartsToRefresh"),
        description: t("dashboard.noChartsToRefreshDesc"),
      });
      return;
    }
    setInsightsGenerating(true);
    try {
      let runningSession = insightsV1SessionId ?? undefined;
      const refreshed: { previousId: string; next: InsightsWidget }[] = [];
      for (const widget of widgetsToRefresh) {
        const res = await insightsV1Api.query({
          prompt: widget.customPrompt!,
          session_id: runningSession,
          id_requisicao: buildInsightsRequestId(),
          locale: insightsApiLocale,
        });
        if (res.session_id) {
          runningSession = res.session_id;
          persistInsightsV1Session(res.session_id);
        }
        if (res.status === "ambiguity") {
          toast({
            title: t("dashboard.ambiguousPrompt"),
            description: res.ambiguity?.message ?? t("dashboard.ambiguousCatalog"),
          });
        } else if (res.status === "degraded") {
          toast({
            title: t("dashboard.partialInsight"),
            description: t("dashboard.partialLowConfidence"),
          });
        }
        const payload = mapInsightV1ResponseToWidget(res, {
          widgetId: widget.id,
          customPrompt: widget.customPrompt,
        });
        refreshed.push({ previousId: widget.id, next: mapApiWidgetToDashboard(payload) });
      }
      setInsightsWidgets((prev) =>
        prev.map((item) => {
          const found = refreshed.find((f) => f.previousId === item.id);
          if (!found) return item;
          return { ...found.next, id: item.id };
        })
      );
      toast({
        title: t("dashboard.updateDone"),
        description: t("dashboard.updateDoneDesc", { count: refreshed.length }),
      });
    } catch (err) {
      toast({
        title: t("dashboard.updateFail"),
        description: err instanceof Error ? err.message : t("dashboard.updateFailDesc"),
        variant: "destructive",
      });
    } finally {
      setInsightsGenerating(false);
    }
  };

  useEffect(() => {
    if (!insightsDragging) return;
    const onMove = (e: MouseEvent) => {
      setInsightsPositions((pos) => {
        const cur = pos[insightsDragging.id] ?? { x: 0, y: 0 };
        return { ...pos, [insightsDragging.id]: { x: cur.x + e.clientX - insightsDragging.startX, y: cur.y + e.clientY - insightsDragging.startY } };
      });
      setInsightsDragging((d) => d ? { ...d, startX: e.clientX, startY: e.clientY } : null);
    };
    const onUp = () => setInsightsDragging(null);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [insightsDragging]);

  useEffect(() => {
    if (!insightsPanning) return;
    const onMove = (e: MouseEvent) => {
      setInsightsPan((p) => ({
        x: insightsPanning.startPanX + (e.clientX - insightsPanning.startX),
        y: insightsPanning.startPanY + (e.clientY - insightsPanning.startY),
      }));
    };
    const onUp = () => setInsightsPanning(null);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [insightsPanning]);

  const insightsFilteredWidgets = insightsFilter === "all"
    ? insightsWidgets
    : insightsWidgets.filter((w) => (w.serviceFilter ?? "data") === insightsFilter);

  useEffect(() => {
    const filtered =
      insightsFilter === "all"
        ? insightsWidgets
        : insightsWidgets.filter((w) => (w.serviceFilter ?? "data") === insightsFilter);
    const ids = filtered.map((w) => w.id);
    if (ids.length === 0) {
      setInsightsActiveChartTab(null);
      return;
    }
    setInsightsActiveChartTab((cur) => (cur && ids.includes(cur) ? cur : ids[0]));
  }, [insightsFilter, insightsWidgets]);

  const INSIGHTS_CARD_FOCUS_W = 320;
  const INSIGHTS_CARD_FOCUS_H = 220;

  const focusInsightsWidgetIntoView = useCallback((id: string) => {
    const container = insightsZoomContainerRef.current;
    if (!container) return;
    const pos = insightsPositions[id] ?? { x: 0, y: 0 };
    const z = insightsZoom;
    const W = container.clientWidth;
    const H = container.clientHeight;
    const cx = pos.x + INSIGHTS_CARD_FOCUS_W / 2;
    const cy = pos.y + INSIGHTS_CARD_FOCUS_H / 2;
    setInsightsPan({
      x: W / 2 - cx * z,
      y: H / 2 - cy * z,
    });
  }, [insightsPositions, insightsZoom]);

  const handleCustomizeSubmit = () => {
    if (!customizeWidgetId) return;
    const prompt = customizeForm.prompt.trim();
    const service = customizeForm.service;
    setInsightsWidgets((prev) =>
      prev.map((w) => {
        if (w.id !== customizeWidgetId) return w;
        const generated = prompt
          ? {
              title: prompt.slice(0, 40) + (prompt.length > 40 ? "…" : ""),
              insights: [
                `Análise gerada a partir do pedido: "${prompt.slice(0, 80)}${prompt.length > 80 ? "…" : ""}".`,
                "Conectado ao serviço selecionado. Dados podem ser refinados ao atualizar.",
              ],
              analysisSummary: `Gráfico customizado: ${prompt.slice(0, 100)}${prompt.length > 100 ? "…" : ""}.`,
              technicalConclusion: "Conclusão técnica será preenchida quando o modelo de dados estiver integrado.",
            }
          : {};
        return {
          ...w,
          serviceFilter: service === "custom" ? "custom" : service,
          customPrompt: prompt || undefined,
          ...generated,
        };
      })
    );
    setCustomizeWidgetId(null);
    toast({
      title: t("dashboard.chartUpdated"),
      description: prompt ? t("dashboard.chartUpdatedAnalysis") : t("dashboard.chartUpdatedPrefs"),
    });
    emitPulsoNotification({
      title: t("notifications.insightTitle"),
      body: (prompt ? t("dashboard.chartUpdatedAnalysis") : t("dashboard.chartUpdatedPrefs")).slice(0, 350),
      kind: "update",
    });
  };

  const handleInsightsCreateFromChat = async (prompt: string): Promise<{
    ok: boolean;
    chartTitle: string;
    chartType: AnalyticsChartType;
    service: ServiceKey | "custom";
  }> => {
    const defaultService: ServiceKey | "custom" = insightsFilter === "custom" ? "custom" : insightsFilter === "all" ? "data" : insightsFilter;
    const id = `widget-${Date.now()}`;
    const newIndex = insightsWidgets.length;
    setInsightsGenerating(true);
    try {
      const res = await insightsV1Api.query({
        prompt,
        session_id: insightsV1SessionId ?? undefined,
        id_requisicao: buildInsightsRequestId(),
        locale: insightsApiLocale,
      });
      persistInsightsV1Session(res.session_id);
      if (res.status === "ambiguity") {
        toast({
          title: t("dashboard.ambiguousPrompt"),
          description: res.ambiguity?.message ?? t("dashboard.ambiguousSuggestions"),
        });
        emitPulsoNotification({
          title: t("dashboard.ambiguousPrompt"),
          body: (res.ambiguity?.message ?? t("dashboard.ambiguousSuggestions")).slice(0, 350),
          kind: "update",
        });
      } else if (res.status === "degraded") {
        toast({
          title: t("dashboard.partialInsight"),
          description: t("dashboard.partialRefine"),
        });
        emitPulsoNotification({
          title: t("dashboard.partialInsight"),
          body: t("dashboard.partialRefine").slice(0, 350),
          kind: "update",
        });
      }
      const payload = mapInsightV1ResponseToWidget(res, { widgetId: id, customPrompt: prompt });
      const mapped = mapApiWidgetToDashboard(payload);
      setInsightsWidgets((prev) => [...prev, { ...mapped, id }]);
      if (insightsLayoutMode === "free") {
        setInsightsPositions((pos) => ({ ...pos, [id]: { x: 20 + (newIndex % 3) * 280, y: 20 + Math.floor(newIndex / 3) * 200 } }));
      }
      toast({ title: t("dashboard.chartAdded"), description: t("dashboard.chartAddedDesc", { title: mapped.title }) });
      emitPulsoNotification({
        title: t("notifications.insightNewTitle"),
        body: t("dashboard.chartAddedDesc", { title: mapped.title }).slice(0, 350),
        kind: "success",
      });
      return {
        ok: true,
        chartTitle: mapped.title,
        chartType: mapped.chartType,
        service: (mapped.serviceFilter ?? defaultService) as ServiceKey | "custom",
      };
    } catch (err) {
      toast({
        title: t("dashboard.backendInsightFail"),
        description: t("dashboard.backendInsightFallback"),
      });
      emitPulsoNotification({
        title: t("dashboard.backendInsightFail"),
        body: t("dashboard.backendInsightFallback").slice(0, 300),
        kind: "error",
      });
      const fbLocale = i18n.language?.replace(/_/g, "-") || "pt-BR";
      const title = prompt.length > 36 ? prompt.slice(0, 36) + "…" : prompt;
      const fallbackData = [
        { label: "P1", value: 120 },
        { label: "P2", value: 180 },
        { label: "P3", value: 145 },
        { label: "P4", value: 220 },
      ];
      setInsightsWidgets((prev) => [
        ...prev,
        {
          id,
          title,
          value: String(fallbackData.reduce((a, d) => a + d.value, 0).toLocaleString(fbLocale)),
          trend: "+0%",
          period: t("dashboard.periodChatGenerated"),
          chartType: "bar",
          insights: [err instanceof Error ? err.message : "Erro ao conectar com o backend de insights."],
          serviceFilter: defaultService,
          customPrompt: prompt,
          analysisSummary: `Análise: ${prompt.slice(0, 80)}${prompt.length > 80 ? "…" : ""}.`,
          technicalConclusion: "Fallback local utilizado por indisponibilidade temporária do backend.",
          data: fallbackData,
        },
      ]);
      if (insightsLayoutMode === "free") {
        setInsightsPositions((pos) => ({ ...pos, [id]: { x: 20 + (newIndex % 3) * 280, y: 20 + Math.floor(newIndex / 3) * 200 } }));
      }
      return {
        ok: false,
        chartTitle: title,
        chartType: "bar",
        service: defaultService,
      };
    } finally {
      setInsightsGenerating(false);
    }
  };

  const submitInsightsPromptWithHistory = async (prompt: string) => {
    if (isGenericCreateChartPrompt(prompt)) {
      const serviceHint =
        insightsFilter === "all"
          ? t("dashboard.serviceHintAll")
          : insightsFilter === "custom"
            ? insightsServiceLabels.custom
            : insightsServiceLabels[insightsFilter];
      const guidance = [
        t("dashboard.guidanceIntro"),
        t("dashboard.guidanceService", { hint: serviceHint }),
        t("dashboard.guidanceChartType"),
        t("dashboard.guidanceGoal"),
      ].join("\n");
      setInsightsChatHistory((prev) => [
        ...prev,
        {
          id: `hist-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          prompt,
          createdAt: Date.now(),
          status: "orientacao",
          assistantMessage: guidance,
        },
      ]);
      toast({
        title: t("dashboard.detailsNeededTitle"),
        description: t("dashboard.detailsNeededDesc"),
      });
      return;
    }

    const historyId = `hist-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setInsightsChatHistory((prev) => [
      ...prev,
      { id: historyId, prompt, createdAt: Date.now(), status: "gerando" },
    ]);
    const result = await handleInsightsCreateFromChat(prompt);
    const serviceLabel = insightsServiceLabels[result.service];
    const chartLabel = insightsChartLabels[result.chartType];
    const assistantMessage = t("dashboard.assistantOutcome", {
      service: serviceLabel,
      chart: chartLabel,
      prompt,
      result: result.ok ? t("dashboard.outcomeOk") : t("dashboard.outcomeFallback"),
    });
    setInsightsChatHistory((prev) =>
      prev.map((item) =>
        item.id === historyId
          ? {
              ...item,
              status: result.ok ? "criado" : "fallback",
              chartTitle: result.chartTitle,
              assistantMessage,
            }
          : item
      )
    );
  };

  const handleInsightsAddConnection = (fromId: string, toId: string) => {
    const id = [fromId, toId].sort().join("--");
    if (insightsConnections.some((c) => c.id === id || (c.from === fromId && c.to === toId))) return;
    setInsightsConnections((prev) => [
      ...prev,
      { id: `conn-${Date.now()}`, from: fromId, to: toId, summary: t("dashboard.connectionSummaryDefault") },
    ]);
    toast({ title: t("dashboard.connectionCreated"), description: t("dashboard.connectionCreatedDesc") });
  };

  const handleExportInsights = () => {
    const expLocale = i18n.language?.replace(/_/g, "-") || "pt-BR";
    const lines: string[] = [
      t("dashboard.exportMdHeader"),
      "",
      `${t("dashboard.exportMdExportedAt")} ${new Date().toLocaleString(expLocale)}`,
      "",
    ];
    insightsWidgets.forEach((w) => {
      lines.push(`## ${w.title}`);
      lines.push(`- Valor: ${w.value} | Tendência: ${w.trend} | Período: ${w.period}`);
      lines.push(t("dashboard.exportMdInsights"));
      w.insights.forEach((i) => lines.push(`- ${i}`));
      lines.push("");
    });
    const content = lines.join("\n");
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dashboard-insights-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast({ title: t("dashboard.exportDone"), description: t("dashboard.exportDoneDesc") });
  };

  const renderServiceContent = () => {
    if (activeService === "pulso") {
      return (
        <div className="pulso-csa-global-scroll flex-1 min-h-0 flex flex-col overflow-y-auto overflow-x-hidden overscroll-y-contain [scrollbar-gutter:stable] animate-slide-up">
          {showLogs && (
            <div className="shrink-0 w-full">
              <LogsPanel />
            </div>
          )}
          {showPreview && previewFrontendUrl && (
            <div className="rounded-lg border border-border bg-card p-4 shrink-0">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-primary shrink-0" />
                  <span className="truncate">{t("dashboard.previewTitle")}</span>
                </h3>
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="pulso"
                    size="sm"
                    onClick={handleTestarPreview}
                    disabled={previewStartLoading || !rootPathForPreview?.trim()}
                    title={
                      !rootPathForPreview?.trim()
                        ? t("dashboard.previewTooltipNoPath")
                        : t("dashboard.previewTooltipDev")
                    }
                  >
                    {previewStartLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                    ) : (
                      <Play className="h-3.5 w-3.5 mr-1.5" />
                    )}
                    {t("dashboard.testPreview")}
                  </Button>
                  <Button
                    variant="pulso"
                    size="sm"
                    onClick={() => window.open(previewFrontendUrl, "_blank")}
                  >
                    {t("dashboard.openNewTab")}
                  </Button>
                </div>
              </div>
              <div className="rounded-lg overflow-hidden border border-border bg-muted/30" style={{ height: "400px" }}>
                <iframe
                  src={previewFrontendUrl}
                  className="w-full h-full border-0"
                  title={t("dashboard.iframeTitle")}
                  sandbox="allow-scripts allow-same-origin"
                />
              </div>
            </div>
          )}
          <div className="shrink-0 w-full min-h-[min(360px,45dvh)] h-[min(72dvh,820px)] max-h-[85dvh]">
            <PromptPanel
              onComprehensionResult={(r) => {
                setPreviewFrontendUrl(r.preview_frontend_url ?? null);
                setRootPathForPreview(r.root_path ?? null);
              }}
              onClear={() => {
                setPreviewFrontendUrl(null);
                setRootPathForPreview(null);
              }}
              toolbarExtra={
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    className="pulso-suggestion-btn flex items-center gap-1.5 h-8 text-xs shrink-0 text-foreground"
                    onClick={() => setShowLogs(!showLogs)}
                  >
                    <Terminal className="h-3.5 w-3.5" />
                    <span>{t("dashboard.logs")}</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!previewFrontendUrl || !rootPathForPreview?.trim() || previewStartLoading}
                    className="pulso-suggestion-btn flex items-center gap-1.5 h-8 text-xs shrink-0 text-foreground"
                    onClick={handleTestarPreview}
                    title={
                      !rootPathForPreview?.trim()
                        ? t("dashboard.previewTooltipNoPath")
                        : t("dashboard.previewTooltipDevShort")
                    }
                  >
                    {previewStartLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Play className="h-3.5 w-3.5" />
                    )}
                    <span>{t("dashboard.testPreview")}</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!previewFrontendUrl}
                    className="pulso-suggestion-btn flex items-center gap-1.5 h-8 text-xs shrink-0 text-foreground"
                    onClick={() => setShowPreview((p) => !p)}
                  >
                    <Monitor className="h-3.5 w-3.5" />
                    <span>{t("dashboard.preview")}</span>
                  </Button>
                </>
              }
            />
          </div>
        </div>
      );
    }
    if (activeService === "cloud") return <div className="flex-1 h-full min-h-0 flex flex-col overflow-hidden"><CloudChat /></div>;
    if (activeService === "finops") return <div className="flex-1 h-full min-h-0 flex flex-col overflow-hidden"><FinOpsChat /></div>;
    if (activeService === "data") return <div className="flex-1 h-full min-h-0 flex flex-col overflow-hidden"><DataChat /></div>;

    const insightsFilterSpacerPx = insightsFilterDockHeight > 0 ? insightsFilterDockHeight : 72;

    return (
      <div className="pulso-insights-screen flex-1 min-h-0 flex flex-col overflow-hidden relative">
        <div ref={insightsFilterDockRef} className="pulso-insights-filter-bar-dock">
          <div className="pulso-insights-filter-row py-2 sm:py-2.5">
            {insightsFilterButtons.map(({ key, icon: Icon, label }) => (
              <button
                key={key}
                type="button"
                data-pulso-tab={key}
                onClick={() => setInsightsFilter(key)}
                className={cn(
                  "pulso-layout-a-btn pulso-layout-a-btn-horizontal shrink-0 text-foreground gap-1.5 px-2.5 sm:px-3 h-9 min-w-[36px] text-xs",
                  insightsFilter === key && "pulso-insights-navbar-btn-filter-active"
                )}
                title={label}
                aria-label={t("dashboard.filterAria", { label })}
                aria-pressed={insightsFilter === key}
              >
                <Icon className="shrink-0 h-4 w-4 pulso-service-tab-icon" strokeWidth={1.5} />
                <span className="font-medium whitespace-nowrap text-xs">{label}</span>
              </button>
            ))}
            <button
              type="button"
              data-pulso-tab="export"
              onClick={handleExportInsights}
              className="pulso-layout-a-btn pulso-layout-a-btn-horizontal shrink-0 text-foreground gap-1.5 px-2.5 sm:px-3 min-w-[36px] h-9 w-auto text-xs"
              title={t("dashboard.exportReportTitle")}
              aria-label={t("dashboard.exportReportAria")}
            >
              <Download className="h-4 w-4 shrink-0 pulso-service-tab-icon" strokeWidth={1.5} />
              <span className="font-medium whitespace-nowrap">{t("dashboard.export")}</span>
            </button>
          </div>
        </div>
        {/* Conteúdo rolável (cards + zoom); espaçador alinha com a barra fixa de filtros */}
        <div className="flex-1 min-h-0 overflow-auto px-4 pb-4 flex flex-col">
          <div
            className="shrink-0 w-full"
            style={{ height: `calc(10px + ${insightsFilterSpacerPx}px)` }}
            aria-hidden
          />
        {insightsFilteredWidgets.length > 0 && (
          <div
            className="shrink-0 flex flex-wrap items-stretch justify-center gap-1.5 pb-2 mb-1 border-b border-border/50"
            role="tablist"
            aria-label={t("dashboard.chartTabsAria")}
          >
            {insightsFilteredWidgets.map((w) => (
              <button
                key={w.id}
                type="button"
                role="tab"
                aria-selected={insightsActiveChartTab === w.id}
                onClick={() => {
                  setInsightsActiveChartTab(w.id);
                  focusInsightsWidgetIntoView(w.id);
                }}
                className={cn(
                  "shrink-0 max-w-[200px] truncate rounded-md border px-3 py-2 text-left text-xs font-medium transition-colors",
                  insightsActiveChartTab === w.id
                    ? "border-primary bg-primary/15 text-primary shadow-sm"
                    : "border-border/60 bg-card/80 text-foreground hover:bg-muted/80"
                )}
                title={w.title}
              >
                {w.title}
              </button>
            ))}
          </div>
        )}
        <div
          ref={insightsZoomContainerRef}
          className={cn(
            "flex-1 min-h-0 overflow-hidden",
            insightsLayoutMode === "free" && (insightsPanning ? "cursor-grabbing" : "cursor-grab"),
            insightsLayoutMode === "grid" && "cursor-context-menu"
          )}
          style={{ minHeight: 200 }}
          onMouseDown={(e) => {
            if (e.button !== 0 || insightsLayoutMode !== "free") return;
            if ((e.target as HTMLElement).closest(".pulso-metric-card")) return;
            setInsightsPanning({ startX: e.clientX, startY: e.clientY, startPanX: insightsPan.x, startPanY: insightsPan.y });
          }}
        >
          <div
            className="flex-1 min-h-0"
            style={{
              transform: `translate(${insightsPan.x}px, ${insightsPan.y}px) scale(${insightsZoom})`,
              transformOrigin: "0 0",
              width: `${100 / insightsZoom}%`,
              height: `${100 / insightsZoom}%`,
              minHeight: (200 / insightsZoom),
            }}
          >
            {insightsLayoutMode === "grid" ? (
              <div className="pulso-insights-grid h-full min-h-[200px]">
                {insightsFilteredWidgets.map((w) => (
                  <ContextMenu key={w.id}>
                    <ContextMenuTrigger asChild>
                      <div className="h-full min-h-0">
                        <AnalyticsCard
                          title={w.title}
                          value={w.value}
                          trend={w.trend}
                          period={w.period}
                          chartType={w.chartType}
                          progressPercent={w.progressPercent}
                          data={w.data}
                          compact
                          insight={w.insights.length ? w.insights : undefined}
                          analysisSummary={w.analysisSummary}
                          technicalConclusion={w.technicalConclusion}
                          className="pulso-metric-card pulso-insights-card"
                        />
                      </div>
                    </ContextMenuTrigger>
                    <ContextMenuContent className="w-56 pulso-dropdown-menu-glass">
                      <ContextMenuSub>
                        <ContextMenuSubTrigger>
                          <Plus className="mr-2 h-4 w-4" />
                          {t("dashboard.createChart")}
                        </ContextMenuSubTrigger>
                        <ContextMenuSubContent className="pulso-dropdown-menu-glass">
                          {insightsChartTypeOptions.map(({ type, label, icon: Icon }) => (
                            <ContextMenuItem key={type} onClick={() => { handleInsightsCreateChart(type); setInsightsMenuOpen(false); }}>
                              <Icon className="mr-2 h-4 w-4" />
                              {label}
                            </ContextMenuItem>
                          ))}
                        </ContextMenuSubContent>
                      </ContextMenuSub>
                      <ContextMenuItem onClick={() => { setCustomizeWidgetId(w.id); setCustomizeForm({ service: (w.serviceFilter ?? "data") as ServiceKey | "custom", prompt: w.customPrompt ?? "" }); }}>
                        <SlidersHorizontal className="mr-2 h-4 w-4" />
                        {t("dashboard.customize")}
                      </ContextMenuItem>
                      <ContextMenuItem onClick={() => { handleInsightsUpdateChart(); setInsightsMenuOpen(false); }}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        {t("dashboard.refresh")}
                      </ContextMenuItem>
                      <ContextMenuSeparator />
                      <ContextMenuSub>
                        <ContextMenuSubTrigger>
                          <Link2 className="mr-2 h-4 w-4" />
                          {t("dashboard.connectTo")}
                        </ContextMenuSubTrigger>
                        <ContextMenuSubContent className="pulso-dropdown-menu-glass">
                          {insightsWidgets.filter((o) => o.id !== w.id).map((other) => (
                            <ContextMenuItem key={other.id} onClick={() => handleInsightsAddConnection(w.id, other.id)}>
                              {other.title}
                            </ContextMenuItem>
                          ))}
                        </ContextMenuSubContent>
                      </ContextMenuSub>
                      <ContextMenuSeparator />
                      <ContextMenuItem onClick={() => handleInsightsDeleteChart(w.id)} className="text-destructive focus:text-destructive">
                        <Trash2 className="mr-2 h-4 w-4" />
                        {t("dashboard.deleteChart")}
                      </ContextMenuItem>
                    </ContextMenuContent>
                  </ContextMenu>
                ))}
              </div>
            ) : (
              <div className="relative w-full h-full min-h-[400px]" style={{ width: "100%", minHeight: 400 }}>
                {/* Cordas entre gráficos conectados */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                      <polygon points="0 0, 10 3.5, 0 7" fill="hsl(var(--primary) / 0.6)" />
                    </marker>
                  </defs>
                  {insightsConnections
                    .filter((c) => insightsFilteredWidgets.some((w) => w.id === c.from) && insightsFilteredWidgets.some((w) => w.id === c.to))
                    .map((c) => {
                      const posA = insightsPositions[c.from] ?? { x: 0, y: 0 };
                      const posB = insightsPositions[c.to] ?? { x: 0, y: 0 };
                      const cx1 = posA.x + 160;
                      const cy1 = posA.y + 90;
                      const cx2 = posB.x + 160;
                      const cy2 = posB.y + 90;
                      const isHovered = connectionHoverId === c.id;
                      return (
                        <g
                          key={c.id}
                          pointerEvents="stroke"
                          style={{ cursor: "pointer" }}
                          onMouseEnter={() => setConnectionHoverId(c.id)}
                          onMouseLeave={() => setConnectionHoverId(null)}
                        >
                          <line
                            x1={cx1}
                            y1={cy1}
                            x2={cx2}
                            y2={cy2}
                            stroke="hsl(var(--primary) / 0.5)"
                            strokeWidth={isHovered ? 12 : 6}
                            strokeLinecap="round"
                          />
                          <line x1={cx1} y1={cy1} x2={cx2} y2={cy2} stroke="hsl(var(--primary))" strokeWidth={2} strokeLinecap="round" markerEnd="url(#arrowhead)" />
                        </g>
                      );
                    })}
                </svg>
                {connectionHoverId && (() => {
                  const c = insightsConnections.find((x) => x.id === connectionHoverId);
                  if (!c) return null;
                  const posA = insightsPositions[c.from] ?? { x: 0, y: 0 };
                  const cx = (posA.x + 160 + (insightsPositions[c.to]?.x ?? 0) + 160) / 2;
                  const cy = (posA.y + 90 + (insightsPositions[c.to]?.y ?? 0) + 90) / 2;
                  return (
                    <div
                      className="absolute z-20 px-3 py-2 rounded-lg bg-popover border border-border shadow-lg text-xs text-foreground max-w-[220px] pointer-events-none"
                      style={{ left: cx - 110, top: cy - 40 }}
                    >
                      {c.summary ?? t("dashboard.connectionSummaryDefault")}
                    </div>
                  );
                })()}
                {insightsFilteredWidgets.map((w) => {
                  const pos = insightsPositions[w.id] ?? { x: 0, y: 0 };
                  const zTab =
                    insightsDragging?.id === w.id ? 20 : insightsActiveChartTab === w.id ? 12 : 1;
                  return (
                    <div
                      key={w.id}
                      className={cn(
                        "absolute cursor-grab active:cursor-grabbing rounded-md transition-shadow duration-150",
                        insightsActiveChartTab === w.id &&
                          "ring-2 ring-primary/55 ring-offset-2 ring-offset-background/0"
                      )}
                      style={{ left: pos.x, top: pos.y, width: 320, zIndex: zTab }}
                      onMouseDown={(e) => {
                        if (e.button !== 0) return;
                        setInsightsActiveChartTab(w.id);
                        setInsightsDragging({ id: w.id, startX: e.clientX, startY: e.clientY, posX: pos.x, posY: pos.y });
                      }}
                    >
                      <ContextMenu>
                        <ContextMenuTrigger asChild>
                          <div className="w-full h-full">
                            <AnalyticsCard
                              title={w.title}
                              value={w.value}
                              trend={w.trend}
                              period={w.period}
                              chartType={w.chartType}
                              progressPercent={w.progressPercent}
                              data={w.data}
                              compact
                              insight={w.insights.length ? w.insights : undefined}
                              analysisSummary={w.analysisSummary}
                              technicalConclusion={w.technicalConclusion}
                              className="pulso-metric-card pulso-insights-card"
                            />
                          </div>
                        </ContextMenuTrigger>
                        <ContextMenuContent className="w-56 pulso-dropdown-menu-glass">
                          <ContextMenuSub>
                            <ContextMenuSubTrigger>
                              <Plus className="mr-2 h-4 w-4" />
                              {t("dashboard.createChart")}
                            </ContextMenuSubTrigger>
                            <ContextMenuSubContent className="pulso-dropdown-menu-glass">
                              {insightsChartTypeOptions.map(({ type, label, icon: Icon }) => (
                                <ContextMenuItem key={type} onClick={() => { handleInsightsCreateChart(type); setInsightsMenuOpen(false); }}>
                                  <Icon className="mr-2 h-4 w-4" />
                                  {label}
                                </ContextMenuItem>
                              ))}
                            </ContextMenuSubContent>
                          </ContextMenuSub>
                          <ContextMenuItem onClick={() => setCustomizeWidgetId(w.id)}>
                            <SlidersHorizontal className="mr-2 h-4 w-4" />
                            {t("dashboard.customize")}
                          </ContextMenuItem>
                          <ContextMenuItem onClick={() => { handleInsightsUpdateChart(); setInsightsMenuOpen(false); }}>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            {t("dashboard.refresh")}
                          </ContextMenuItem>
                          <ContextMenuSeparator />
                          <ContextMenuSub>
                            <ContextMenuSubTrigger>
                              <Link2 className="mr-2 h-4 w-4" />
                              {t("dashboard.connectTo")}
                            </ContextMenuSubTrigger>
                            <ContextMenuSubContent className="pulso-dropdown-menu-glass">
                              {insightsWidgets.filter((o) => o.id !== w.id).map((other) => (
                                <ContextMenuItem key={other.id} onClick={() => handleInsightsAddConnection(w.id, other.id)}>
                                  {other.title}
                                </ContextMenuItem>
                              ))}
                            </ContextMenuSubContent>
                          </ContextMenuSub>
                          <ContextMenuSeparator />
                          <ContextMenuItem onClick={() => handleInsightsDeleteChart(w.id)} className="text-destructive focus:text-destructive">
                            <Trash2 className="mr-2 h-4 w-4" />
                            {t("dashboard.deleteChart")}
                          </ContextMenuItem>
                        </ContextMenuContent>
                      </ContextMenu>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
        </div>
        {/* Chatbot popup para criar insights em linguagem natural */}
        {activeService === null && (
          <>
            <div className="pulso-insights-chat-launcher">
              <ul>
                <li
                  style={{ ["--i" as string]: "#905DED", ["--j" as string]: "#4F9FF3" }}
                  onClick={() => setInsightsChatOpen(true)}
                  aria-label={t("dashboard.chatLauncherAria")}
                  title={t("dashboard.chatLauncherTitle")}
                >
                  <span className="icon">
                    <MessageCircle className="h-6 w-6" />
                  </span>
                  <span className="title">{t("dashboard.messages")}</span>
                </li>
              </ul>
            </div>
            <Dialog open={insightsChatOpen} onOpenChange={setInsightsChatOpen}>
              <DialogContent className="sm:max-w-2xl pulso-insights-chat-dialog text-card-foreground">
                <DialogHeader>
                  <DialogTitle className="text-xl font-semibold text-foreground">
                    {t("dashboard.chatTitle")}
                  </DialogTitle>
                </DialogHeader>
                <div className="pulso-insights-chat-history">
                  {insightsChatHistory.length === 0 ? (
                    <p className="text-sm text-foreground/75 leading-relaxed pulso-insights-chat-empty">
                      {t("dashboard.chatEmpty")}
                    </p>
                  ) : (
                    insightsChatHistory.map((item) => (
                      <div key={item.id} className="space-y-1">
                        <div className="pulso-insights-chat-user-bubble">
                          <p className="text-sm text-foreground font-medium">{item.prompt}</p>
                        </div>
                        <div className="pulso-insights-chat-assistant-bubble">
                          <p className="text-xs text-foreground/70 pulso-insights-chat-assistant-status">
                            {item.status === "gerando" && t("dashboard.statusGenerating")}
                            {item.status === "criado" &&
                              t("dashboard.statusCreated", { title: item.chartTitle ?? t("dashboard.newChartFallback") })}
                            {item.status === "fallback" &&
                              t("dashboard.statusFallback", { title: item.chartTitle ?? t("dashboard.newChartFallback") })}
                            {item.status === "orientacao" && t("dashboard.statusGuidance")}
                          </p>
                          {item.assistantMessage && (
                            <p className="text-sm text-foreground mt-2 whitespace-pre-line leading-relaxed">
                              {item.assistantMessage}
                            </p>
                          )}
                          {(item.status === "criado" || item.status === "fallback") && (
                            <div className="mt-2">
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs pulso-insights-chat-repeat-btn"
                                onClick={() => {
                                  void submitInsightsPromptWithHistory(item.prompt);
                                }}
                                disabled={insightsGenerating}
                              >
                                {t("dashboard.useAgain")}
                              </Button>
                            </div>
                          )}
                        </div>
                        <p className="text-[10px] text-foreground/55 px-1 tabular-nums">
                          {new Date(item.createdAt).toLocaleTimeString(i18n.language?.replace(/_/g, "-") || "pt-BR")}
                        </p>
                      </div>
                    ))
                  )}
                </div>
                <InsightsChatBar
                  catalogSuggestions={insightsCatalogSuggestions}
                  onSubmit={(prompt) => {
                    void submitInsightsPromptWithHistory(prompt);
                  }}
                  disabled={insightsLoading || insightsGenerating}
                  placeholder={
                    insightsGenerating ? t("dashboard.statusGenerating") : t("dashboard.chatPlaceholder")
                  }
                />
              </DialogContent>
            </Dialog>
          </>
        )}
        {/* Barra de zoom: canto inferior central */}
        {activeService === null && (
          <div className="absolute bottom-[6.5rem] left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 px-4 py-2 rounded-full bg-background/90 backdrop-blur border border-border shadow-lg min-w-[200px] max-w-[280px]">
            <span className="text-xs text-muted-foreground whitespace-nowrap">{t("dashboard.zoom")}</span>
            <Slider
              value={[insightsZoom]}
              onValueChange={([v]) => setInsightsZoom(Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, v)))}
              min={ZOOM_MIN}
              max={ZOOM_MAX}
              step={ZOOM_STEP}
              className="flex-1"
            />
            <span className="text-xs font-mono text-foreground w-10 text-right">{Math.round(insightsZoom * 100)}%</span>
          </div>
        )}
        {activeService === null && (
          <InsightsFab
            open={insightsMenuOpen}
            onOpenChange={setInsightsMenuOpen}
            onZoomIn={handleInsightsZoomIn}
            onZoomOut={handleInsightsZoomOut}
            onCreateChart={handleInsightsCreateChart}
            onDeleteChart={handleInsightsDeleteChart}
            onUpdateChart={handleInsightsUpdateChart}
            widgetIds={insightsWidgets.map((w) => ({ id: w.id, title: w.title }))}
            zoomLevel={insightsZoom}
          />
        )}
      </div>
    );
  };

  const serviceErrorFallback = (
    <div className="pulso-empty-state">
      <p className="pulso-empty-state-title">{t("dashboard.serviceErrorTitle")}</p>
      <p className="pulso-empty-state-desc mb-4">{t("dashboard.serviceErrorDesc")}</p>
      <Button variant="pulso" onClick={() => window.location.reload()} className="gap-2">
        <RefreshCw className="h-4 w-4" />
        {t("dashboard.reloadPage")}
      </Button>
    </div>
  );

  const content = (
    <ErrorBoundary fallback={serviceErrorFallback}>
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <div
          key={activeService ?? "welcome"}
          className="flex-1 min-h-0 flex flex-col overflow-hidden animate-service-transition"
        >
          {renderServiceContent()}
        </div>
      </div>
    </ErrorBoundary>
  );

  return (
    <>
      <ShortcutsModal open={showShortcuts} onOpenChange={setShowShortcuts} />
      <Dialog open={!!customizeWidgetId} onOpenChange={(open) => !open && setCustomizeWidgetId(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("dashboard.customizeTitle")}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="customize-service">{t("dashboard.connectService")}</Label>
              <Select
                value={customizeForm.service}
                onValueChange={(v) => setCustomizeForm((f) => ({ ...f, service: v as ServiceKey | "custom" }))}
              >
                <SelectTrigger id="customize-service" aria-label={t("dashboard.connectServiceAria")}>
                  <SelectValue placeholder={t("dashboard.selectService")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pulso">{insightsServiceLabels.pulso}</SelectItem>
                  <SelectItem value="cloud">{insightsServiceLabels.cloud}</SelectItem>
                  <SelectItem value="finops">{insightsServiceLabels.finops}</SelectItem>
                  <SelectItem value="data">{insightsServiceLabels.data}</SelectItem>
                  <SelectItem value="custom">{insightsServiceLabels.custom}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="customize-prompt">{t("dashboard.customPromptLabel")}</Label>
              <Textarea
                id="customize-prompt"
                placeholder={t("dashboard.customPromptPlaceholder")}
                value={customizeForm.prompt}
                onChange={(e) => setCustomizeForm((f) => ({ ...f, prompt: e.target.value }))}
                rows={4}
                className="resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCustomizeWidgetId(null)}>
              {t("profile.cancel")}
            </Button>
            <Button variant="pulso" onClick={handleCustomizeSubmit}>
              {t("dashboard.generateChart")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <LayoutA
        className="pulso-layout-a--chat-scroll-lock"
        activeService={activeService}
        onServiceChange={setActiveService}
      >
        {content}
      </LayoutA>
    </>
  );
};

export default Dashboard;
