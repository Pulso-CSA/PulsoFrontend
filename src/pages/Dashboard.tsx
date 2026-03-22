import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Monitor, Terminal, RefreshCw, Download, Workflow, CloudCog, TrendingDown, Brain, SlidersHorizontal, LayoutGrid, Plus, Trash2, Link2, Play, Loader2, Activity, BarChart3, TrendingUp, Circle, Percent, MessageCircle, type LucideIcon } from "lucide-react";
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
import { previewApi, insightsApi, type InsightsWidgetResponse } from "@/lib/api";

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
};

type InsightsChatHistoryItem = {
  id: string;
  prompt: string;
  createdAt: number;
  status: "gerando" | "criado" | "fallback" | "orientacao";
  chartTitle?: string;
  assistantMessage?: string;
};

const INSIGHTS_WIDGETS_INITIAL: InsightsWidget[] = [
  { id: "post-views", title: "Post Views", value: "2,012", trend: "+12.3%", period: "Últimas 24h", chartType: "area", insights: ["O pico de visualizações ocorre entre 12h e 14h.", "Considere agendar posts nesse horário para maximizar alcance."], serviceFilter: "pulso", analysisSummary: "Visualizações de posts ao longo do dia.", technicalConclusion: "Pico entre 12h–14h; recomendado agendar publicações nesse intervalo." },
  { id: "conversoes", title: "Conversões", value: "1,245", trend: "+8.1%", period: "Últimos 7 dias", chartType: "bar", insights: ["Taxa de conversão está acima da média do setor.", "O funil sugere que o checkout pode ser simplificado."], serviceFilter: "data", analysisSummary: "Conversões por período.", technicalConclusion: "Taxa acima da média; oportunidade de simplificar checkout." },
  { id: "sales", title: "Sales", value: "39,500", trend: "+20%", period: "Este mês", chartType: "progress", progressPercent: 76, insights: ["Volume de conversas está estável nesta semana.", "Tempo médio de resposta pode ser reduzido com automação."], serviceFilter: "finops", analysisSummary: "Progresso de vendas no mês.", technicalConclusion: "Volume estável; automação pode reduzir tempo de resposta." },
];

const INSIGHTS_CHART_TYPE_OPTIONS: {
  type: AnalyticsChartType;
  label: string;
  icon: LucideIcon;
}[] = [
  { type: "area", label: "Gráfico de área", icon: Activity },
  { type: "bar", label: "Gráfico de barras", icon: BarChart3 },
  { type: "line", label: "Gráfico de linha", icon: TrendingUp },
  { type: "pie", label: "Gráfico de pizza", icon: Circle },
  { type: "progress", label: "Gráfico de progresso", icon: Percent },
];

const INSIGHTS_SERVICE_LABELS: Record<ServiceKey | "custom", string> = {
  pulso: "Pulso CSA",
  cloud: "Cloud IaC",
  finops: "FinOps",
  data: "Dados & IA",
  custom: "Personalizado",
};

const INSIGHTS_CHART_LABELS: Record<AnalyticsChartType, string> = {
  area: "Área",
  bar: "Barras",
  line: "Linha",
  pie: "Pizza",
  progress: "Progresso",
};

const buildInsightsRequestId = () =>
  (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
    ? crypto.randomUUID()
    : `ins-${Date.now()}`;

const mapApiWidgetToDashboard = (widget: InsightsWidgetResponse): InsightsWidget => ({
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
});

const isGenericCreateChartPrompt = (prompt: string) => {
  const p = prompt.trim().toLowerCase();
  if (!p) return true;
  return /^(criar|gere|gerar|montar|fazer)?\s*(um\s*)?(gr[aá]fico|grafico|insight)(\s*por\s*chat)?[.!?]*$/.test(p);
};

const Dashboard = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const [activeService, setActiveService] = useState<ServiceKey | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [previewFrontendUrl, setPreviewFrontendUrlState] = useState<string | null>(
    () => localStorage.getItem("pulso_preview_frontend_url")
  );
  const [rootPathForPreview, setRootPathForPreview] = useState<string | null>(null);
  const [previewStartLoading, setPreviewStartLoading] = useState(false);

  const [insightsWidgets, setInsightsWidgets] = useState<InsightsWidget[]>(() => INSIGHTS_WIDGETS_INITIAL);
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
  const [connectionHoverId, setConnectionHoverId] = useState<string | null>(null);
  const [customizeWidgetId, setCustomizeWidgetId] = useState<string | null>(null);
  const [customizeForm, setCustomizeForm] = useState<{ service: ServiceKey | "custom"; prompt: string }>({ service: "data", prompt: "" });
  const INSIGHTS_ZOOM_MIN = 0.5;
  const INSIGHTS_ZOOM_MAX = 2;
  const insightsZoomContainerRef = useRef<HTMLDivElement>(null);
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
        title: "Caminho da pasta necessário",
        description: "Configure o caminho da pasta do projeto na seção Configuração antes de testar o preview.",
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
        const msg = res.message ?? "Servidor de desenvolvimento iniciado. O preview estará disponível em breve.";
        toast({
          title: "Preview iniciado",
          description: (
            <>
              {msg}
              {previewUrl && (
                <>
                  {" "}
                  <a href={previewUrl} target="_blank" rel="noopener noreferrer" className="text-primary underline font-medium hover:underline">
                    Acessar preview
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
          title: "Erro ao iniciar preview",
          description: res.message ?? (res.details != null ? String(res.details) : "Tente novamente."),
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: "Erro ao iniciar preview",
        description: err instanceof Error ? err.message : "Falha ao conectar com o backend.",
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
        title: "Checkout concluído",
        description: "Sua assinatura foi ativada com sucesso!",
      });
      setSearchParams({}, { replace: true });
    } else if (checkout === "cancel") {
      toast({
        title: "Checkout cancelado",
        description: "Você pode tentar novamente quando quiser.",
        variant: "destructive",
      });
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, toast]);

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

  useEffect(() => {
    let cancelled = false;
    const loadInsightsWidgets = async () => {
      setInsightsLoading(true);
      try {
        const res = await insightsApi.listWidgets();
        if (cancelled || !res.widgets?.length) return;
        setInsightsWidgets(res.widgets.map(mapApiWidgetToDashboard));
      } catch (err) {
        if (cancelled) return;
        toast({
          title: "Insights com dados locais",
          description: err instanceof Error ? err.message : "Não foi possível carregar os widgets do backend.",
        });
      } finally {
        if (!cancelled) setInsightsLoading(false);
      }
    };
    loadInsightsWidgets();
    return () => {
      cancelled = true;
    };
  }, [toast]);

  const ZOOM_MIN = 0.5;
  const ZOOM_MAX = 2;
  const ZOOM_STEP = 0.1;

  const handleInsightsZoomIn = () => setInsightsZoom((z) => Math.min(ZOOM_MAX, z + ZOOM_STEP));
  const handleInsightsZoomOut = () => setInsightsZoom((z) => Math.max(ZOOM_MIN, z - ZOOM_STEP));
  const handleInsightsCreateChart = (chartType: AnalyticsChartType = "area") => {
    const chartLabelMap: Record<AnalyticsChartType, string> = {
      area: "Área",
      bar: "Barras",
      line: "Linha",
      pie: "Pizza",
      progress: "Progresso",
    };
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
    const value = isProgressChart
      ? "65%"
      : String(chartData.reduce((acc, item) => acc + item.value, 0).toLocaleString("pt-BR"));

    const id = `widget-${Date.now()}`;
    const newIndex = insightsWidgets.length;
    const defaultService: ServiceKey | "custom" = insightsFilter === "custom" ? "custom" : insightsFilter === "all" ? "data" : insightsFilter;
    setInsightsWidgets((prev) => [
      ...prev,
      {
        id,
        title: `Novo gráfico (${chartLabelMap[chartType]})`,
        value,
        trend: "+0%",
        period: "Agora",
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
    toast({ title: "Gráfico criado", description: `Tipo selecionado: ${chartLabelMap[chartType]}.` });
  };
  const handleInsightsDeleteChart = (id: string) => {
    setInsightsWidgets((prev) => prev.filter((w) => w.id !== id));
    setInsightsPositions((pos) => {
      const next = { ...pos };
      delete next[id];
      return next;
    });
    setInsightsConnections((prev) => prev.filter((c) => c.from !== id && c.to !== id));
    toast({ title: "Gráfico excluído", variant: "destructive" });
  };
  const handleInsightsUpdateChart = async () => {
    const widgetsToRefresh = insightsWidgets.filter((w) => !!w.customPrompt?.trim());
    if (!widgetsToRefresh.length) {
      toast({
        title: "Sem gráficos para atualizar",
        description: "Crie ao menos um gráfico via chat para atualizar com dados do backend.",
      });
      return;
    }
    setInsightsGenerating(true);
    try {
      const refreshed = await Promise.all(
        widgetsToRefresh.map(async (widget) => {
          const res = await insightsApi.generateWidget({
            prompt: widget.customPrompt!,
            id_requisicao: buildInsightsRequestId(),
            service_filter: (widget.serviceFilter ?? "data") as "pulso" | "cloud" | "finops" | "data" | "custom",
          });
          return { previousId: widget.id, next: mapApiWidgetToDashboard(res.widget) };
        })
      );
      setInsightsWidgets((prev) =>
        prev.map((item) => {
          const found = refreshed.find((f) => f.previousId === item.id);
          if (!found) return item;
          return { ...found.next, id: item.id };
        })
      );
      toast({ title: "Atualização concluída", description: `${refreshed.length} gráfico(s) atualizado(s).` });
    } catch (err) {
      toast({
        title: "Falha ao atualizar insights",
        description: err instanceof Error ? err.message : "Tente novamente em instantes.",
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
    toast({ title: "Gráfico atualizado", description: prompt ? "Análise gerada conforme sua descrição." : "Serviço e preferências salvos." });
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
      const res = await insightsApi.generateWidget({
        prompt,
        id_requisicao: buildInsightsRequestId(),
        service_filter: defaultService,
      });
      const mapped = mapApiWidgetToDashboard(res.widget);
      setInsightsWidgets((prev) => [...prev, { ...mapped, id }]);
      if (insightsLayoutMode === "free") {
        setInsightsPositions((pos) => ({ ...pos, [id]: { x: 20 + (newIndex % 3) * 280, y: 20 + Math.floor(newIndex / 3) * 200 } }));
      }
      toast({ title: "Gráfico criado", description: `"${mapped.title}" adicionado ao dashboard.` });
      return {
        ok: true,
        chartTitle: mapped.title,
        chartType: mapped.chartType,
        service: (mapped.serviceFilter ?? defaultService) as ServiceKey | "custom",
      };
    } catch (err) {
      toast({
        title: "Falha ao gerar insight no backend",
        description: "Usando gráfico local de fallback para não interromper o fluxo.",
      });
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
          value: String(fallbackData.reduce((a, d) => a + d.value, 0).toLocaleString("pt-BR")),
          trend: "+0%",
          period: "Gerado por chat",
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
      const serviceHint = insightsFilter === "all"
        ? "Todos (ou selecione Pulso CSA, Cloud IaC, FinOps, Dados & IA)"
        : insightsFilter === "custom"
          ? "Personalizado"
          : INSIGHTS_SERVICE_LABELS[insightsFilter];
      const guidance = [
        "Para criar de forma autônoma, me diga:",
        `1) Serviço: ${serviceHint}`,
        "2) Tipo de gráfico: área, barras, linha, pizza ou progresso",
        "3) Objetivo do gráfico: ex. comparar custo por cloud, monitorar churn, evolução de receita",
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
        title: "Detalhes necessários para criar o gráfico",
        description: "Informe serviço, tipo e objetivo para geração autônoma.",
      });
      return;
    }

    const historyId = `hist-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setInsightsChatHistory((prev) => [
      ...prev,
      { id: historyId, prompt, createdAt: Date.now(), status: "gerando" },
    ]);
    const result = await handleInsightsCreateFromChat(prompt);
    const serviceLabel = INSIGHTS_SERVICE_LABELS[result.service];
    const chartLabel = INSIGHTS_CHART_LABELS[result.chartType];
    const outcome = result.ok ? "criado com sucesso" : "criado com fallback local";
    const assistantMessage = `Serviço selecionado: ${serviceLabel}. Tipo definido: ${chartLabel}. Objetivo interpretado: ${prompt}. Resultado: ${outcome}.`;
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
    setInsightsConnections((prev) => [...prev, { id: `conn-${Date.now()}`, from: fromId, to: toId, summary: `Análise de correlação entre os gráficos.` }]);
    toast({ title: "Conexão criada", description: "Os dois gráficos estão conectados para análise." });
  };

  const handleExportInsights = () => {
    const lines: string[] = ["# Dashboard de Insights", "", `Exportado em: ${new Date().toLocaleString("pt-BR")}`, ""];
    insightsWidgets.forEach((w) => {
      lines.push(`## ${w.title}`);
      lines.push(`- Valor: ${w.value} | Tendência: ${w.trend} | Período: ${w.period}`);
      lines.push("### Insights");
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
    toast({ title: "Dashboard exportado", description: "Arquivo baixado com sucesso." });
  };

  const renderServiceContent = () => {
    if (activeService === "pulso") {
      return (
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden animate-slide-up">
          {showLogs && <LogsPanel />}
          {showPreview && previewFrontendUrl && (
            <div className="rounded-lg border border-border bg-card p-4 shrink-0">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-primary shrink-0" />
                  <span className="truncate">Preview do Frontend</span>
                </h3>
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="pulso"
                    size="sm"
                    onClick={handleTestarPreview}
                    disabled={previewStartLoading || !rootPathForPreview?.trim()}
                    title={!rootPathForPreview?.trim() ? "Configure o caminho da pasta na seção Configuração" : "Inicia npm run dev ou streamlit em background"}
                  >
                    {previewStartLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                    ) : (
                      <Play className="h-3.5 w-3.5 mr-1.5" />
                    )}
                    Testar Preview
                  </Button>
                  <Button
                    variant="pulso"
                    size="sm"
                    onClick={() => window.open(previewFrontendUrl, "_blank")}
                  >
                    Abrir em nova aba
                  </Button>
                </div>
              </div>
              <div className="rounded-lg overflow-hidden border border-border bg-muted/30" style={{ height: "400px" }}>
                <iframe
                  src={previewFrontendUrl}
                  className="w-full h-full border-0"
                  title="Preview do Frontend"
                  sandbox="allow-scripts allow-same-origin"
                />
              </div>
            </div>
          )}
          <div className="flex-1 min-h-0 overflow-hidden">
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
                    className="pulso-suggestion-btn flex items-center gap-1.5 h-8 text-xs shrink-0 text-white"
                    onClick={() => setShowLogs(!showLogs)}
                  >
                    <Terminal className="h-3.5 w-3.5" />
                    <span>Logs</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!previewFrontendUrl || !rootPathForPreview?.trim() || previewStartLoading}
                    className="pulso-suggestion-btn flex items-center gap-1.5 h-8 text-xs shrink-0 text-white"
                    onClick={handleTestarPreview}
                    title={!rootPathForPreview?.trim() ? "Configure o caminho da pasta na seção Configuração" : "Inicia o servidor de desenvolvimento (npm run dev)"}
                  >
                    {previewStartLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Play className="h-3.5 w-3.5" />
                    )}
                    <span>Testar Preview</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!previewFrontendUrl}
                    className="pulso-suggestion-btn flex items-center gap-1.5 h-8 text-xs shrink-0 text-white"
                    onClick={() => setShowPreview((p) => !p)}
                  >
                    <Monitor className="h-3.5 w-3.5" />
                    <span>Preview</span>
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

    const INSIGHTS_FILTER_BUTTONS: { key: InsightsFilterKey; icon: LucideIcon; label: string }[] = [
      { key: "all", icon: LayoutGrid, label: "Todos" },
      { key: "pulso", icon: Workflow, label: "Pulso CSA" },
      { key: "cloud", icon: CloudCog, label: "Cloud IaC" },
      { key: "finops", icon: TrendingDown, label: "FinOps" },
      { key: "data", icon: Brain, label: "Dados & IA" },
      { key: "custom", icon: SlidersHorizontal, label: "Personalizado" },
    ];

    return (
      <div className="pulso-insights-screen flex-1 min-h-0 flex flex-col overflow-hidden relative">
        {/* Conteúdo rolável (cards + zoom) */}
        <div className="flex-1 min-h-0 overflow-auto px-4 pb-4 flex flex-col">
        <div className="flex flex-wrap items-center gap-2 py-3">
          {INSIGHTS_FILTER_BUTTONS.map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setInsightsFilter(key)}
              className={cn(
                "pulso-layout-a-btn pulso-layout-a-btn-horizontal text-white gap-1.5 px-3 h-9 min-w-[36px] text-xs",
                insightsFilter === key && "pulso-insights-navbar-btn-filter-active"
              )}
              title={label}
              aria-label={`Filtrar: ${label}`}
              aria-pressed={insightsFilter === key}
            >
              <Icon className="shrink-0 h-4 w-4" strokeWidth={1.5} />
              <span className="font-medium whitespace-nowrap text-xs">{label}</span>
            </button>
          ))}
          <button
            type="button"
            onClick={handleExportInsights}
            className="pulso-layout-a-btn pulso-layout-a-btn-horizontal text-white gap-1.5 px-3 min-w-[36px] h-9 w-auto text-xs"
            title="Baixar relatório"
            aria-label="Baixar relatório do dashboard"
          >
            <Download className="h-4 w-4 shrink-0" strokeWidth={1.5} />
            <span className="font-medium whitespace-nowrap">Exportar</span>
          </button>
        </div>
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
                          Criar gráfico
                        </ContextMenuSubTrigger>
                        <ContextMenuSubContent className="pulso-dropdown-menu-glass">
                          {INSIGHTS_CHART_TYPE_OPTIONS.map(({ type, label, icon: Icon }) => (
                            <ContextMenuItem key={type} onClick={() => { handleInsightsCreateChart(type); setInsightsMenuOpen(false); }}>
                              <Icon className="mr-2 h-4 w-4" />
                              {label}
                            </ContextMenuItem>
                          ))}
                        </ContextMenuSubContent>
                      </ContextMenuSub>
                      <ContextMenuItem onClick={() => { setCustomizeWidgetId(w.id); setCustomizeForm({ service: (w.serviceFilter ?? "data") as ServiceKey | "custom", prompt: w.customPrompt ?? "" }); }}>
                        <SlidersHorizontal className="mr-2 h-4 w-4" />
                        Customizar
                      </ContextMenuItem>
                      <ContextMenuItem onClick={() => { handleInsightsUpdateChart(); setInsightsMenuOpen(false); }}>
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Atualizar
                      </ContextMenuItem>
                      <ContextMenuSeparator />
                      <ContextMenuSub>
                        <ContextMenuSubTrigger>
                          <Link2 className="mr-2 h-4 w-4" />
                          Conectar a...
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
                        Excluir gráfico
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
                      {c.summary ?? "Análise de correlação entre os dois gráficos."}
                    </div>
                  );
                })()}
                {insightsFilteredWidgets.map((w) => {
                  const pos = insightsPositions[w.id] ?? { x: 0, y: 0 };
                  return (
                    <div
                      key={w.id}
                      className="absolute cursor-grab active:cursor-grabbing"
                      style={{ left: pos.x, top: pos.y, width: 320, zIndex: insightsDragging?.id === w.id ? 10 : 1 }}
                      onMouseDown={(e) => {
                        if (e.button !== 0) return;
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
                              Criar gráfico
                            </ContextMenuSubTrigger>
                            <ContextMenuSubContent className="pulso-dropdown-menu-glass">
                              {INSIGHTS_CHART_TYPE_OPTIONS.map(({ type, label, icon: Icon }) => (
                                <ContextMenuItem key={type} onClick={() => { handleInsightsCreateChart(type); setInsightsMenuOpen(false); }}>
                                  <Icon className="mr-2 h-4 w-4" />
                                  {label}
                                </ContextMenuItem>
                              ))}
                            </ContextMenuSubContent>
                          </ContextMenuSub>
                          <ContextMenuItem onClick={() => setCustomizeWidgetId(w.id)}>
                            <SlidersHorizontal className="mr-2 h-4 w-4" />
                            Customizar
                          </ContextMenuItem>
                          <ContextMenuItem onClick={() => { handleInsightsUpdateChart(); setInsightsMenuOpen(false); }}>
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Atualizar
                          </ContextMenuItem>
                          <ContextMenuSeparator />
                          <ContextMenuSub>
                            <ContextMenuSubTrigger>
                              <Link2 className="mr-2 h-4 w-4" />
                              Conectar a...
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
                            Excluir gráfico
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
                  aria-label="Abrir chatbot de insights"
                  title="Criar gráfico por chat"
                >
                  <span className="icon">
                    <MessageCircle className="h-6 w-6" />
                  </span>
                  <span className="title">Messages</span>
                </li>
              </ul>
            </div>
            <Dialog open={insightsChatOpen} onOpenChange={setInsightsChatOpen}>
              <DialogContent className="sm:max-w-2xl pulso-insights-chat-dialog">
                <DialogHeader>
                  <DialogTitle>Criar gráfico por chat</DialogTitle>
                </DialogHeader>
                <div className="pulso-insights-chat-history">
                  {insightsChatHistory.length === 0 ? (
                    <p className="text-xs text-muted-foreground">
                      Histórico da sessão aparecerá aqui. Envie um prompt para gerar seu primeiro gráfico.
                    </p>
                  ) : (
                    insightsChatHistory.map((item) => (
                      <div key={item.id} className="space-y-1">
                        <div className="pulso-insights-chat-user-bubble">
                          <p className="text-sm text-foreground">{item.prompt}</p>
                        </div>
                        <div className="pulso-insights-chat-assistant-bubble">
                          <p className="text-xs text-muted-foreground">
                            {item.status === "gerando" && "Gerando insight no backend..."}
                            {item.status === "criado" && `Gráfico criado: ${item.chartTitle ?? "Novo gráfico"}`}
                            {item.status === "fallback" && `Fallback local aplicado: ${item.chartTitle ?? "Novo gráfico"}`}
                            {item.status === "orientacao" && "Detalhes necessários para criação autônoma."}
                          </p>
                          {item.assistantMessage && (
                            <p className="text-xs text-foreground/90 mt-2 whitespace-pre-line leading-relaxed">
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
                                Usar novamente
                              </Button>
                            </div>
                          )}
                        </div>
                        <p className="text-[10px] text-muted-foreground px-1">
                          {new Date(item.createdAt).toLocaleTimeString("pt-BR")}
                        </p>
                      </div>
                    ))
                  )}
                </div>
                <InsightsChatBar
                  onSubmit={(prompt) => {
                    void submitInsightsPromptWithHistory(prompt);
                  }}
                  disabled={insightsLoading || insightsGenerating}
                  placeholder={insightsGenerating ? "Gerando insight no backend..." : "Ex: vendas por região, churn mensal, evolução de receita..."}
                />
              </DialogContent>
            </Dialog>
          </>
        )}
        {/* Barra de zoom: canto inferior central */}
        {activeService === null && (
          <div className="absolute bottom-[6.5rem] left-1/2 -translate-x-1/2 z-40 flex items-center gap-3 px-4 py-2 rounded-full bg-background/90 backdrop-blur border border-border shadow-lg min-w-[200px] max-w-[280px]">
            <span className="text-xs text-muted-foreground whitespace-nowrap">Zoom</span>
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
      <p className="pulso-empty-state-title">Erro ao carregar o serviço</p>
      <p className="pulso-empty-state-desc mb-4">Ocorreu um problema. Tente recarregar ou selecione outro serviço.</p>
      <Button variant="pulso" onClick={() => window.location.reload()} className="gap-2">
        <RefreshCw className="h-4 w-4" />
        Recarregar página
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
            <DialogTitle>Customizar gráfico</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="customize-service">Serviço ao qual conectar</Label>
              <Select
                value={customizeForm.service}
                onValueChange={(v) => setCustomizeForm((f) => ({ ...f, service: v as ServiceKey | "custom" }))}
              >
                <SelectTrigger id="customize-service" aria-label="Serviço ao qual conectar">
                  <SelectValue placeholder="Selecione o serviço" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pulso">Pulso CSA</SelectItem>
                  <SelectItem value="cloud">Cloud IaC</SelectItem>
                  <SelectItem value="finops">FinOps</SelectItem>
                  <SelectItem value="data">Dados & IA</SelectItem>
                  <SelectItem value="custom">Personalizado</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="customize-prompt">O que você quer que este gráfico seja?</Label>
              <Textarea
                id="customize-prompt"
                placeholder='Ex: "Correlacionar variável X e Y"; "Analisar se meus clientes estão se evadindo"; "Projeções de churn para o mês que vem"'
                value={customizeForm.prompt}
                onChange={(e) => setCustomizeForm((f) => ({ ...f, prompt: e.target.value }))}
                rows={4}
                className="resize-none"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCustomizeWidgetId(null)}>
              Cancelar
            </Button>
            <Button variant="pulso" onClick={handleCustomizeSubmit}>
              Gerar gráfico
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <LayoutA
        className={cn(activeService === null && "pulso-layout-a--chat-scroll-lock")}
        activeService={activeService}
        onServiceChange={setActiveService}
      >
        {content}
      </LayoutA>
    </>
  );
};

export default Dashboard;
