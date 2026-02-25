import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Monitor, Terminal, LayoutGrid, PanelLeft, LayoutDashboard, LayoutList, Minus } from "lucide-react";
import { Button } from "@/components/ui/button";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { ShortcutsModal } from "@/components/dashboard/ShortcutsModal";
import { DashboardLayoutCompact, type LayerKey } from "@/components/dashboard/DashboardLayoutCompact";
import { DashboardLayoutBento } from "@/components/dashboard/DashboardLayoutBento";
import { DashboardLayoutDense } from "@/components/dashboard/DashboardLayoutDense";
import { DashboardLayoutMinimal } from "@/components/dashboard/DashboardLayoutMinimal";
import { useToast } from "@/hooks/use-toast";
import PromptPanel from "@/components/dashboard/PromptPanel";
import LogsPanel from "@/components/dashboard/LogsPanel";
import FinOpsChat from "@/components/dashboard/FinOpsChat";
import DataChat from "@/components/dashboard/DataChat";
import CloudChat from "@/components/dashboard/CloudChat";

const LAYOUT_KEY = "pulso_layout_mode";
type LayoutMode = "grid" | "compact" | "bento" | "dense" | "minimal";

const LAYOUT_CYCLE: LayoutMode[] = ["grid", "compact", "bento", "dense", "minimal"];
const LAYOUT_LABELS: Record<LayoutMode, string> = {
  grid: "Grid",
  compact: "Sidebar",
  bento: "Bento",
  dense: "Denso",
  minimal: "Minimal",
};

const Dashboard = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const [layoutMode, setLayoutMode] = useState<LayoutMode>(() => {
    const stored = localStorage.getItem(LAYOUT_KEY);
    if (["grid", "compact", "bento", "dense", "minimal"].includes(stored ?? "")) return stored as LayoutMode;
    return "grid";
  });
  const [compactActiveLayer, setCompactActiveLayer] = useState<LayerKey | null>(null);
  const [activeLayers, setActiveLayers] = useState({
    preview: false,
    pulso: false,
    finops: false,
    data: false,
    cloud: false,
  });
  const [showLogs, setShowLogs] = useState(false);
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

  return (
    <div className="min-h-screen flex flex-col bg-background relative overflow-hidden">
      {/* Background — semiesferas PULSO (gradiente roxo→ciano conforme App.png) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 pulso-orb animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 pulso-orb animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 pulso-orb-sm animate-pulse" style={{ animationDelay: "2s" }} />
      </div>

      <div className="relative z-10">
        <DashboardHeader
          activeLayers={activeLayers}
          setActiveLayers={setActiveLayers}
          onShortcutsClick={() => setShowShortcuts(true)}
          hideLayerSelection={!["grid"].includes(layoutMode)}
          layoutToggle={
            <div className="flex items-center rounded-lg border border-border/60 bg-muted/30 p-0.5 shrink-0" role="group" aria-label="Seleção de layout">
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 transition-all duration-200 ${
                  layoutMode === "grid" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => {
                  setLayoutMode("grid");
                  localStorage.setItem(LAYOUT_KEY, "grid");
                  toast({ title: "Layout: Grid", description: "Grid central" });
                }}
                title="Grid"
                aria-label="Layout Grid"
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 transition-all duration-200 ${
                  layoutMode === "compact" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => {
                  setLayoutMode("compact");
                  localStorage.setItem(LAYOUT_KEY, "compact");
                  toast({ title: "Layout: Sidebar", description: "Sidebar lateral" });
                }}
                title="Sidebar"
                aria-label="Layout Sidebar"
              >
                <PanelLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 transition-all duration-200 ${
                  layoutMode === "bento" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => {
                  setLayoutMode("bento");
                  localStorage.setItem(LAYOUT_KEY, "bento");
                  toast({ title: "Layout: Bento", description: "Grade Bento" });
                }}
                title="Bento"
                aria-label="Layout Bento"
              >
                <LayoutDashboard className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 transition-all duration-200 ${
                  layoutMode === "dense" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => {
                  setLayoutMode("dense");
                  localStorage.setItem(LAYOUT_KEY, "dense");
                  toast({ title: "Layout: Denso", description: "Analítico, sidebar colapsável" });
                }}
                title="Denso (Layout A)"
                aria-label="Layout Denso"
              >
                <LayoutList className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 transition-all duration-200 ${
                  layoutMode === "minimal" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => {
                  setLayoutMode("minimal");
                  localStorage.setItem(LAYOUT_KEY, "minimal");
                  toast({ title: "Layout: Minimal", description: "Um foco por vez" });
                }}
                title="Minimal (Layout C)"
                aria-label="Layout Minimal"
              >
                <Minus className="h-4 w-4" />
              </Button>
            </div>
          }
        />
      </div>
      <ShortcutsModal open={showShortcuts} onOpenChange={setShowShortcuts} />
      
      <main id="main-content" className="flex-1 relative z-10" tabIndex={-1}>
        <div key={layoutMode} className="h-full animate-fluid-fade">
        {layoutMode === "compact" ? (
          <DashboardLayoutCompact
            activeLayer={compactActiveLayer}
            onLayerChange={(layer) => {
              setCompactActiveLayer(layer);
              if (layer) {
                setActiveLayers({
                  preview: false,
                  pulso: layer === "pulso",
                  finops: layer === "finops",
                  data: layer === "data",
                  cloud: layer === "cloud",
                });
              } else {
                setActiveLayers({ preview: false, pulso: false, finops: false, data: false, cloud: false });
              }
            }}
          >
            <div className="container mx-auto p-4 lg:p-6">
              {compactActiveLayer === "pulso" && (
                <div className="space-y-4 animate-slide-up">
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" size="sm" className="flex items-center gap-2 transition-all duration-300 ease-out hover:scale-[1.02]" onClick={() => setShowLogs(!showLogs)}>
                      <Terminal className="h-4 w-4" />
                      <span>Logs</span>
                    </Button>
                    <Button variant="outline" size="sm" disabled={!previewFrontendUrl} className="transition-all duration-300 ease-out hover:scale-[1.02]" onClick={() => setActiveLayers(prev => ({ ...prev, preview: !prev.preview }))}>
                      <Monitor className="h-4 w-4" />
                      <span>Preview</span>
                    </Button>
                  </div>
                  {showLogs && <LogsPanel />}
                  <PromptPanel onComprehensionResult={(r) => setPreviewFrontendUrl(r.preview_frontend_url ?? null)} onClear={() => setPreviewFrontendUrl(null)} />
                </div>
              )}
              {compactActiveLayer === "cloud" && <CloudChat />}
              {compactActiveLayer === "finops" && <FinOpsChat />}
              {compactActiveLayer === "data" && <DataChat />}
              {!compactActiveLayer && (
                <div className="flex flex-col items-center justify-center min-h-[400px] text-center text-muted-foreground">
                  <p className="text-lg font-medium">Selecione uma camada na barra lateral</p>
                  <p className="text-sm mt-2">Pulso, Cloud, FinOps ou Dados & IA</p>
                </div>
              )}
            </div>
          </DashboardLayoutCompact>
        ) : layoutMode === "bento" ? (
          <DashboardLayoutBento
            activeLayer={compactActiveLayer}
            onLayerChange={(layer) => {
              setCompactActiveLayer(layer);
              if (layer) {
                setActiveLayers({
                  preview: false,
                  pulso: layer === "pulso",
                  finops: layer === "finops",
                  data: layer === "data",
                  cloud: layer === "cloud",
                });
              } else {
                setActiveLayers({ preview: false, pulso: false, finops: false, data: false, cloud: false });
              }
            }}
          >
            <div className="p-4 lg:p-6">
              {compactActiveLayer === "pulso" && (
                <div className="space-y-4 animate-fluid-fade">
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" size="sm" className="flex items-center gap-2 transition-all duration-300 ease-out hover:scale-[1.02]" onClick={() => setShowLogs(!showLogs)}>
                      <Terminal className="h-4 w-4" />
                      <span>Logs</span>
                    </Button>
                    <Button variant="outline" size="sm" disabled={!previewFrontendUrl} className="transition-all duration-300 ease-out hover:scale-[1.02]" onClick={() => setActiveLayers(prev => ({ ...prev, preview: !prev.preview }))}>
                      <Monitor className="h-4 w-4" />
                      <span>Preview</span>
                    </Button>
                  </div>
                  {showLogs && <LogsPanel />}
                  <PromptPanel onComprehensionResult={(r) => setPreviewFrontendUrl(r.preview_frontend_url ?? null)} onClear={() => setPreviewFrontendUrl(null)} />
                </div>
              )}
              {compactActiveLayer === "cloud" && <CloudChat />}
              {compactActiveLayer === "finops" && <FinOpsChat />}
              {compactActiveLayer === "data" && <DataChat />}
            </div>
          </DashboardLayoutBento>
        ) : layoutMode === "dense" ? (
          <DashboardLayoutDense
            activeLayer={compactActiveLayer}
            onLayerChange={(layer) => {
              setCompactActiveLayer(layer);
              if (layer) {
                setActiveLayers({
                  preview: false,
                  pulso: layer === "pulso",
                  finops: layer === "finops",
                  data: layer === "data",
                  cloud: layer === "cloud",
                });
              } else {
                setActiveLayers({ preview: false, pulso: false, finops: false, data: false, cloud: false });
              }
            }}
          >
            <div className="container mx-auto p-4 lg:p-6 overflow-auto">
              {compactActiveLayer === "pulso" && (
                <div className="space-y-4 animate-slide-up">
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" size="sm" className="flex items-center gap-2" onClick={() => setShowLogs(!showLogs)}>
                      <Terminal className="h-4 w-4" />
                      <span>Logs</span>
                    </Button>
                    <Button variant="outline" size="sm" disabled={!previewFrontendUrl} onClick={() => setActiveLayers(prev => ({ ...prev, preview: !prev.preview }))}>
                      <Monitor className="h-4 w-4" />
                      <span>Preview</span>
                    </Button>
                  </div>
                  {showLogs && <LogsPanel />}
                  <PromptPanel onComprehensionResult={(r) => setPreviewFrontendUrl(r.preview_frontend_url ?? null)} onClear={() => setPreviewFrontendUrl(null)} />
                </div>
              )}
              {compactActiveLayer === "cloud" && <CloudChat />}
              {compactActiveLayer === "finops" && <FinOpsChat />}
              {compactActiveLayer === "data" && <DataChat />}
              {!compactActiveLayer && (
                <div className="flex flex-col items-center justify-center min-h-[400px] text-center text-muted-foreground">
                  <p className="text-lg font-medium">Selecione uma camada na barra lateral</p>
                </div>
              )}
            </div>
          </DashboardLayoutDense>
        ) : layoutMode === "minimal" ? (
          <DashboardLayoutMinimal
            activeLayer={compactActiveLayer}
            onLayerChange={(layer) => {
              setCompactActiveLayer(layer);
              if (layer) {
                setActiveLayers({
                  preview: false,
                  pulso: layer === "pulso",
                  finops: layer === "finops",
                  data: layer === "data",
                  cloud: layer === "cloud",
                });
              } else {
                setActiveLayers({ preview: false, pulso: false, finops: false, data: false, cloud: false });
              }
            }}
          >
            <div className="p-4 lg:p-6">
              {compactActiveLayer === "pulso" && (
                <div className="space-y-4">
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" size="sm" onClick={() => setShowLogs(!showLogs)}>
                      <Terminal className="h-4 w-4" />
                      <span>Logs</span>
                    </Button>
                    <Button variant="outline" size="sm" disabled={!previewFrontendUrl} onClick={() => setActiveLayers(prev => ({ ...prev, preview: !prev.preview }))}>
                      <Monitor className="h-4 w-4" />
                      <span>Preview</span>
                    </Button>
                  </div>
                  {showLogs && <LogsPanel />}
                  <PromptPanel onComprehensionResult={(r) => setPreviewFrontendUrl(r.preview_frontend_url ?? null)} onClear={() => setPreviewFrontendUrl(null)} />
                </div>
              )}
              {compactActiveLayer === "cloud" && <CloudChat />}
              {compactActiveLayer === "finops" && <FinOpsChat />}
              {compactActiveLayer === "data" && <DataChat />}
            </div>
          </DashboardLayoutMinimal>
        ) : (
        <div className="flex flex-col gap-6 container mx-auto p-4 lg:p-6">
          <div className="flex-1 space-y-6">
            {activeLayers.pulso && (
              <div className="space-y-4 animate-slide-up">
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className={`flex items-center gap-2 glass glass-hover border-2 transition-all duration-300 ease-out hover:scale-[1.02] ${
                      showLogs
                        ? "border-primary bg-gradient-to-r from-primary/80 to-primary-deep/60 pulso-glow-cta text-white [&>span]:text-white [&>svg]:text-white"
                        : "border-primary/40 hover:border-primary/60"
                    }`}
                    onClick={() => setShowLogs(!showLogs)}
                  >
                    <Terminal className="h-4 w-4" />
                    <span>Controle de Logs</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!previewFrontendUrl}
                    title={previewFrontendUrl ? "Abrir preview da tela de teste" : "Execute um workflow para gerar o preview"}
                    className={`flex items-center gap-2 glass glass-hover border-2 transition-all duration-300 ease-out hover:scale-[1.02] ${
                      activeLayers.preview
                        ? "border-primary bg-gradient-to-r from-primary/80 to-primary-deep/60 pulso-glow-cta text-white [&>span]:text-white [&>svg]:text-white"
                        : previewFrontendUrl
                          ? "border-primary/40 hover:border-primary/60"
                          : "border-primary/20 opacity-60 cursor-not-allowed"
                    }`}
                    onClick={() => previewFrontendUrl && setActiveLayers(prev => ({ ...prev, preview: !prev.preview }))}
                  >
                    <Monitor className="h-4 w-4" />
                    <span>Preview do Frontend</span>
                  </Button>
                </div>
                
                {activeLayers.preview && (
                  <div className="glass-strong rounded-lg p-4 border-2 border-primary/30">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                        <Monitor className="h-4 w-4 text-primary" />
                        Preview do Frontend
                      </h3>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground font-mono px-2 py-1 rounded bg-primary/10">
                          {previewFrontendUrl ?? "localhost:3000"}
                        </span>
                        {previewFrontendUrl && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(previewFrontendUrl, "_blank")}
                            className="h-7 text-xs"
                          >
                            Abrir em nova aba
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="glass rounded-md overflow-hidden border border-primary/30" style={{ height: '600px' }}>
                      {previewFrontendUrl ? (
                        <iframe
                          src={previewFrontendUrl}
                          className="w-full h-full border-0"
                          title="Preview do Frontend"
                          sandbox="allow-scripts allow-same-origin"
                        />
                      ) : (
                        <iframe
                        srcDoc={`
                          <!DOCTYPE html>
                          <html lang="pt-BR">
                          <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>App Demo</title>
                            <style>
                              * { margin: 0; padding: 0; box-sizing: border-box; }
                              body {
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                min-height: 100vh;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                padding: 20px;
                              }
                              .container {
                                background: white;
                                border-radius: 16px;
                                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                                max-width: 500px;
                                width: 100%;
                                padding: 40px;
                              }
                              h1 {
                                color: #1a202c;
                                font-size: 28px;
                                margin-bottom: 10px;
                              }
                              p {
                                color: #718096;
                                margin-bottom: 30px;
                                line-height: 1.6;
                              }
                              .feature {
                                background: #f7fafc;
                                padding: 20px;
                                border-radius: 12px;
                                margin-bottom: 15px;
                                border-left: 4px solid #667eea;
                              }
                              .feature h3 {
                                color: #2d3748;
                                font-size: 16px;
                                margin-bottom: 8px;
                              }
                              .feature p {
                                color: #718096;
                                font-size: 14px;
                                margin: 0;
                              }
                              button {
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                border: none;
                                padding: 14px 28px;
                                border-radius: 8px;
                                font-size: 16px;
                                font-weight: 600;
                                cursor: pointer;
                                width: 100%;
                                margin-top: 20px;
                                transition: transform 0.2s, box-shadow 0.2s;
                              }
                              button:hover {
                                transform: translateY(-2px);
                                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
                              }
                              button:active {
                                transform: translateY(0);
                              }
                            </style>
                          </head>
                          <body>
                            <div class="container">
                              <h1>🚀 Meu App</h1>
                              <p>Este é um exemplo de frontend gerado automaticamente</p>
                              
                              <div class="feature">
                                <h3>✨ Design Moderno</h3>
                                <p>Interface limpa e responsiva</p>
                              </div>
                              
                              <div class="feature">
                                <h3>⚡ Performance</h3>
                                <p>Otimizado para velocidade</p>
                              </div>
                              
                              <div class="feature">
                                <h3>🎯 Componentes</h3>
                                <p>Estrutura organizada e escalável</p>
                              </div>
                              
                              <button onclick="alert('Funcionalidade em desenvolvimento!')">
                                Começar Agora
                              </button>
                            </div>
                          </body>
                          </html>
                        `}
                        className="w-full h-full border-0"
                        title="Frontend Preview"
                        sandbox="allow-scripts"
                      />
                      )}
                    </div>
                  </div>
                )}

                {showLogs && (
                  <LogsPanel />
                )}
                
                <PromptPanel
                  onComprehensionResult={(r) => setPreviewFrontendUrl(r.preview_frontend_url ?? null)}
                  onClear={() => setPreviewFrontendUrl(null)}
                />
              </div>
            )}
            {activeLayers.cloud && <div className="animate-slide-up"><CloudChat /></div>}
            {activeLayers.finops && <div className="animate-slide-up"><FinOpsChat /></div>}
            {activeLayers.data && <div className="animate-slide-up"><DataChat /></div>}
          </div>
        </div>
        )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
