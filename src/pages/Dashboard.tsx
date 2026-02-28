import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Monitor, Terminal, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLayoutContext } from "@/contexts/LayoutContext";
import { LayoutA } from "@/layouts/LayoutA";
import { LayoutB } from "@/layouts/LayoutB";
import type { ServiceKey } from "@/layouts/LayoutA";
import { ShortcutsModal } from "@/components/dashboard/ShortcutsModal";
import { useToast } from "@/hooks/use-toast";
import PromptPanel from "@/components/dashboard/PromptPanel";
import LogsPanel from "@/components/dashboard/LogsPanel";
import FinOpsChat from "@/components/dashboard/FinOpsChat";
import DataChat from "@/components/dashboard/DataChat";
import CloudChat from "@/components/dashboard/CloudChat";
import { AnalyticsCard } from "@/components/dashboard/AnalyticsCard";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const Dashboard = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const { layoutMode } = useLayoutContext();
  const [activeService, setActiveService] = useState<ServiceKey | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [previewFrontendUrl, setPreviewFrontendUrlState] = useState<string | null>(
    () => localStorage.getItem("pulso_preview_frontend_url")
  );

  const setPreviewFrontendUrl = (url: string | null) => {
    setPreviewFrontendUrlState(url);
    if (url) localStorage.setItem("pulso_preview_frontend_url", url);
    else localStorage.removeItem("pulso_preview_frontend_url");
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

  const renderServiceContent = () => {
    if (activeService === "pulso") {
      return (
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden animate-slide-up">
          <div className="flex justify-end gap-3">
            <Button
              variant="pulso"
              size="default"
              className="flex items-center gap-2.5 text-base min-h-[42px] px-5"
              onClick={() => setShowLogs(!showLogs)}
            >
              <Terminal className="h-5 w-5" />
              <span>Logs</span>
            </Button>
            <Button
              variant="pulso"
              size="default"
              disabled={!previewFrontendUrl}
              className="flex items-center gap-2.5 text-base min-h-[42px] px-5"
              onClick={() => setShowPreview((p) => !p)}
            >
              <Monitor className="h-5 w-5" />
              <span>Preview</span>
            </Button>
          </div>
          {showLogs && <LogsPanel />}
          {showPreview && previewFrontendUrl && (
            <div className="rounded-lg border border-border bg-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-foreground flex items-center gap-2.5">
                  <Monitor className="h-5 w-5 text-primary" />
                  Preview do Frontend
                </h3>
                <Button
                  variant="pulso"
                  size="default"
                  onClick={() => window.open(previewFrontendUrl, "_blank")}
                  className="min-h-[38px] px-4 text-sm"
                >
                  Abrir em nova aba
                </Button>
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
              onComprehensionResult={(r) => setPreviewFrontendUrl(r.preview_frontend_url ?? null)}
              onClear={() => setPreviewFrontendUrl(null)}
            />
          </div>
        </div>
      );
    }
    if (activeService === "cloud") return <div className="flex-1 min-h-0 overflow-hidden"><CloudChat /></div>;
    if (activeService === "finops") return <div className="flex-1 min-h-0 overflow-hidden"><FinOpsChat /></div>;
    if (activeService === "data") return <div className="flex-1 min-h-0 overflow-hidden"><DataChat /></div>;

    return (
      <div className="pulso-insights-screen flex-1 min-h-0 flex flex-col overflow-hidden">
        <h2 className="pulso-insights-title flex-shrink-0">Insights</h2>
        <div className="pulso-insights-grid flex-1 min-h-0">
          <AnalyticsCard
            title="Post Views"
            value="2,012"
            trend="+12.3%"
            period="Últimas 24h"
            compact
            insight={[
              "O pico de visualizações ocorre entre 12h e 14h.",
              "Considere agendar posts nesse horário para maximizar alcance.",
              "A tendência de +12.3% indica engajamento crescente.",
              "Compare com métricas de conversão para otimizar CTAs.",
              "Explore segmentação por dispositivo para refinar estratégia.",
            ]}
            className="pulso-metric-card"
          />
          <AnalyticsCard
            title="Conversões"
            value="1,245"
            trend="+8.1%"
            period="Últimos 7 dias"
            compact
            insight={[
              "Taxa de conversão está acima da média do setor.",
              "O funil sugere que o checkout pode ser simplificado.",
              "Usuários mobile convertem 23% menos — priorize UX mobile.",
              "Retargeting nos abandonos pode elevar conversões em 15%.",
              "A/B test em headlines pode melhorar a taxa de clique.",
            ]}
            className="pulso-metric-card"
          />
          <AnalyticsCard
            title="Chats Ativos"
            value="4"
            period="Hoje"
            compact
            insight={[
              "Volume de conversas está estável nesta semana.",
              "Tempo médio de resposta pode ser reduzido com automação.",
              "Identifique padrões nas perguntas para criar FAQs.",
              "Sessões longas indicam alto interesse — qualifique leads.",
              "Considere horários de pico para escalar suporte.",
            ]}
            className="pulso-metric-card"
          />
        </div>
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
      <div key={layoutMode} className="flex-1 min-h-0 flex flex-col overflow-hidden animate-fluid-fade">
        {renderServiceContent()}
      </div>
    </ErrorBoundary>
  );

  return (
    <>
      <ShortcutsModal open={showShortcuts} onOpenChange={setShowShortcuts} />
      {layoutMode === "A" ? (
        <LayoutA activeService={activeService} onServiceChange={setActiveService}>
          {content}
        </LayoutA>
      ) : (
        <LayoutB activeService={activeService} onServiceChange={setActiveService}>
          {content}
        </LayoutB>
      )}
    </>
  );
};

export default Dashboard;
