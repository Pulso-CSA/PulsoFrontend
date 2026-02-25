/**
 * Layout Sidebar — navegação lateral
 * Barra de destaque vertical no item ativo
 */
import { cn } from "@/lib/utils";
import { LAYER_CONFIG, type LayerKey } from "./LayerCard";

const SIDEBAR_SHORT: Record<LayerKey, string> = {
  pulso: "Pulso",
  cloud: "Cloud",
  finops: "FinOps",
  data: "Dados",
};

interface DashboardLayoutCompactProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

export function DashboardLayoutCompact({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutCompactProps) {
  return (
    <div className={cn("flex min-h-[calc(100vh-4rem)]", className)}>
      <aside
        className="w-14 flex flex-col border-r border-border bg-card shrink-0"
        aria-label="Módulos"
      >
        <div className="p-1.5 flex flex-col gap-0.5">
          {LAYER_CONFIG.map(({ key, label, icon: Icon }) => {
            const isActive = activeLayer === key;
            return (
              <button
                key={key}
                onClick={() => onLayerChange(isActive ? null : key)}
                className={cn(
                  "relative flex flex-col items-center gap-1 py-2.5 px-2 rounded-md transition-colors",
                  isActive
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
                title={label}
                aria-pressed={isActive}
                aria-label={`${label} ${isActive ? "ativo" : "inativo"}`}
              >
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-primary rounded-r" />
                )}
                <Icon className="h-5 w-5" strokeWidth={1.5} />
                <span className="text-[10px] font-medium truncate w-full text-center">
                  {SIDEBAR_SHORT[key]}
                </span>
              </button>
            );
          })}
        </div>
      </aside>

      <main className="flex-1 overflow-auto min-w-0 bg-background">
        {children}
      </main>
    </div>
  );
}
