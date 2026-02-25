/**
 * Layout A — Analítico / Denso
 * Grid central, sidebar colapsável, métricas em cards compactos acima do input
 * Uso: power users, análise intensiva
 */
import { useState } from "react";
import { Workflow, TrendingDown, Brain, CloudCog, PanelLeftClose, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";

export type LayerKey = "pulso" | "cloud" | "finops" | "data";

interface DashboardLayoutDenseProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const LAYERS: { key: LayerKey; label: string; icon: typeof Workflow; short: string }[] = [
  { key: "pulso", label: "Pulso CSA", icon: Workflow, short: "Pulso" },
  { key: "cloud", label: "Infra Cloud", icon: CloudCog, short: "Cloud" },
  { key: "finops", label: "FinOps", icon: TrendingDown, short: "FinOps" },
  { key: "data", label: "Dados & IA", icon: Brain, short: "Data" },
];

export function DashboardLayoutDense({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutDenseProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className={cn("flex min-h-[calc(100vh-4rem)]", className)}>
      {/* Sidebar colapsável */}
      <aside
        className={cn(
          "flex flex-col border-r border-border/60 bg-card/40 backdrop-blur-xl shrink-0 transition-all duration-300 ease-out",
          sidebarCollapsed ? "w-14" : "w-20 lg:w-24"
        )}
        aria-label="Seleção de camadas"
      >
        <div className="p-2 flex flex-col gap-1">
          {LAYERS.map(({ key, label, icon: Icon, short }) => (
            <button
              key={key}
              onClick={() => onLayerChange(activeLayer === key ? null : key)}
              className={cn(
                "flex flex-col items-center justify-center gap-1 py-2.5 px-2 rounded-lg transition-all duration-300",
                "hover:scale-105 active:scale-95",
                activeLayer === key
                  ? "bg-primary text-primary-foreground shadow-md scale-105"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              title={label}
              aria-pressed={activeLayer === key}
              aria-label={`${label} ${activeLayer === key ? "ativo" : "inativo"}`}
            >
              <Icon className="h-4 w-4 lg:h-5 lg:w-5" strokeWidth={1.5} />
              {!sidebarCollapsed && (
                <span className="text-[10px] font-medium truncate w-full text-center">{short}</span>
              )}
            </button>
          ))}
        </div>
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="mt-auto p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          title={sidebarCollapsed ? "Expandir sidebar" : "Recolher sidebar"}
          aria-label={sidebarCollapsed ? "Expandir sidebar" : "Recolher sidebar"}
        >
          {sidebarCollapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </aside>

      {/* Área principal — 70% foco em conteúdo */}
      <main className="flex-1 overflow-auto min-w-0 flex flex-col">
        {/* Métricas compactas (cards acima do conteúdo quando aplicável) */}
        {activeLayer && (
          <div className="shrink-0 border-b border-border/40 bg-card/20 px-4 py-2">
            <div className="flex flex-wrap gap-2">
              {LAYERS.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => onLayerChange(activeLayer === key ? null : key)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                    activeLayer === key
                      ? "bg-primary/20 text-primary border border-primary/40"
                      : "text-muted-foreground hover:bg-muted/80 hover:text-foreground"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" strokeWidth={1.5} />
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="flex-1 flex flex-col min-h-0">{children}</div>
      </main>
    </div>
  );
}
