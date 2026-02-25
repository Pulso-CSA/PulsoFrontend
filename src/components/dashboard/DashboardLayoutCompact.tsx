/**
 * Layout alternativo: sidebar compacta para app desktop
 * Navegação lateral em vez de grid central
 */
import { Workflow, TrendingDown, Brain, CloudCog } from "lucide-react";
import { cn } from "@/lib/utils";

export type LayerKey = "pulso" | "cloud" | "finops" | "data";

interface DashboardLayoutCompactProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const LAYERS: { key: LayerKey; label: string; icon: typeof Workflow; short: string }[] = [
  { key: "pulso", label: "Pulso CSA", icon: Workflow, short: "Pulso" },
  { key: "cloud", label: "Infra Cloud", icon: CloudCog, short: "Cloud" },
  { key: "finops", label: "FinOps", icon: TrendingDown, short: "FinOps" },
  { key: "data", label: "Dados & IA", icon: Brain, short: "Dados" },
];

export function DashboardLayoutCompact({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutCompactProps) {
  return (
    <div className={cn("flex min-h-[calc(100vh-4rem)]", className)}>
      {/* Sidebar compacta - transparência, elegância */}
      <aside
        className="w-16 lg:w-20 flex flex-col border-r border-border/60 bg-card/40 backdrop-blur-xl shrink-0 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]"
        aria-label="Seleção de camadas"
      >
        <div className="p-2 flex flex-col gap-1">
          {LAYERS.map(({ key, label, icon: Icon, short }) => (
            <button
              key={key}
              onClick={() => onLayerChange(activeLayer === key ? null : key)}
              className={cn(
                "flex flex-col items-center justify-center gap-1 py-3 px-2 rounded-lg transition-all duration-300 ease-out",
                "hover:scale-105 active:scale-95",
                activeLayer === key
                  ? "bg-primary text-primary-foreground shadow-md scale-105"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              title={label}
              aria-pressed={activeLayer === key}
              aria-label={`${label} ${activeLayer === key ? "ativo" : "inativo"}`}
            >
              <Icon className="h-5 w-5 lg:h-6 lg:w-6" strokeWidth={1.5} />
              <span className="text-[10px] lg:text-xs font-medium truncate w-full text-center">
                {short}
              </span>
            </button>
          ))}
        </div>
      </aside>

      {/* Área principal */}
      <main className="flex-1 overflow-auto min-w-0">
        {children}
      </main>
    </div>
  );
}

