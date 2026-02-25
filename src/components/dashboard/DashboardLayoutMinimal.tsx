/**
 * Layout C — Minimalista / Decisório
 * Um foco por vez, espaço negativo amplo, input mínimo, sem sidebar
 * Uso: decisões rápidas, fluxos simples
 */
import { Workflow, TrendingDown, Brain, CloudCog } from "lucide-react";
import { cn } from "@/lib/utils";

export type LayerKey = "pulso" | "cloud" | "finops" | "data";

interface DashboardLayoutMinimalProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const LAYERS: { key: LayerKey; label: string; desc: string; icon: typeof Workflow }[] = [
  { key: "pulso", label: "Pulso CSA", desc: "Blueprint & Estrutura", icon: Workflow },
  { key: "cloud", label: "Infra Cloud", desc: "AWS, Azure, GCP", icon: CloudCog },
  { key: "finops", label: "FinOps", desc: "Otimização de Custos", icon: TrendingDown },
  { key: "data", label: "Dados & IA", desc: "Analytics e Modelos", icon: Brain },
];

export function DashboardLayoutMinimal({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutMinimalProps) {
  return (
    <div className={cn("min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-8 lg:p-16", className)}>
      {activeLayer ? (
        /* Modo foco: conteúdo centralizado com amplo espaço negativo */
        <div className="w-full max-w-4xl mx-auto space-y-8 animate-fluid-fade">
          <div className="flex justify-center">
            <button
              onClick={() => onLayerChange(null)}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Voltar à seleção"
            >
              ← Trocar camada
            </button>
          </div>
          <div className="rounded-2xl border border-border/60 bg-card/80 backdrop-blur-2xl shadow-2xl overflow-hidden min-h-[480px]">
            {children}
          </div>
        </div>
      ) : (
        /* Modo seleção: apenas os 4 cards, máximo espaço negativo */
        <div className="w-full max-w-2xl space-y-12">
          <p className="text-center text-sm font-medium text-muted-foreground tracking-wide uppercase">
            O que deseja fazer?
          </p>
          <div className="grid grid-cols-2 gap-6">
            {LAYERS.map(({ key, label, desc, icon: Icon }, i) => (
              <button
                key={key}
                onClick={() => onLayerChange(key)}
                className={cn(
                  "group flex flex-col items-center justify-center gap-4 p-8 rounded-2xl",
                  "border border-border/60 bg-card/60 backdrop-blur-xl",
                  "transition-all duration-500 ease-out",
                  "hover:scale-[1.02] hover:shadow-2xl hover:shadow-primary/10 hover:border-primary/40",
                  "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background",
                  "animate-fluid-fade"
                )}
                style={{ animationDelay: `${i * 80}ms`, animationFillMode: "backwards" }}
                aria-label={`Abrir ${label}`}
              >
                <div className="rounded-2xl p-4 bg-primary/10 group-hover:bg-primary/15 transition-colors">
                  <Icon className="h-10 w-10 text-primary" strokeWidth={1.25} />
                </div>
                <div className="text-center space-y-1">
                  <p className="font-semibold text-foreground">{label}</p>
                  <p className="text-xs text-muted-foreground">{desc}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
