/**
 * Layout Minimal — lista vertical centralizada
 * Um foco por vez
 */
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { LAYER_CONFIG, LayerCard, type LayerKey } from "./LayerCard";

interface DashboardLayoutMinimalProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

export function DashboardLayoutMinimal({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutMinimalProps) {
  return (
    <div className={cn("min-h-[calc(100vh-4rem)] flex flex-col items-center p-6 lg:p-12", className)}>
      {activeLayer ? (
        <div className="w-full max-w-3xl mx-auto space-y-6 animate-fluid-fade">
          <button
            onClick={() => onLayerChange(null)}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            aria-label="Voltar"
          >
            <ArrowLeft className="h-4 w-4" />
            Trocar módulo
          </button>
          <div className="rounded-lg border border-border bg-card overflow-hidden min-h-[480px]">
            {children}
          </div>
        </div>
      ) : (
        <div className="w-full max-w-md space-y-6">
          <div className="text-center">
            <h2 className="text-sm font-medium text-foreground">O que deseja fazer?</h2>
            <p className="text-xs text-muted-foreground mt-1">Escolha um módulo</p>
          </div>
          <div className="flex flex-col gap-2">
            {LAYER_CONFIG.map((layer) => (
              <LayerCard
                key={layer.key}
                layer={layer}
                isActive={false}
                onClick={() => onLayerChange(layer.key)}
                variant="minimal"
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
