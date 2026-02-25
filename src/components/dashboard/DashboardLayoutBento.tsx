/**
 * Layout Bento - grade premium com cards que expandem
 * Surpreendente, elegante, fácil de usar
 */
import { Workflow, TrendingDown, Brain, CloudCog, X, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export type LayerKey = "pulso" | "cloud" | "finops" | "data";

interface DashboardLayoutBentoProps {
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

export function DashboardLayoutBento({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutBentoProps) {
  return (
    <div className={cn("min-h-[calc(100vh-4rem)] p-4 lg:p-8", className)}>
      <div className="max-w-7xl mx-auto">
        {activeLayer ? (
          /* Modo expandido: card ativo em destaque */
          <div className="space-y-5 animate-fluid-fade">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-xl p-2 bg-primary/10">
                  {(() => {
                    const layer = LAYERS.find((l) => l.key === activeLayer);
                    const Icon = layer?.icon ?? Workflow;
                    return <Icon className="h-5 w-5 text-primary" strokeWidth={1.5} />;
                  })()}
                </div>
                <h2 className="text-xl font-semibold tracking-tight text-foreground">
                  {LAYERS.find((l) => l.key === activeLayer)?.label}
                </h2>
              </div>
              <button
                onClick={() => onLayerChange(null)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-all duration-300 ease-out"
                aria-label="Voltar à grade"
              >
                <span className="text-sm font-medium">Voltar</span>
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="rounded-2xl border border-border/60 bg-card/90 backdrop-blur-2xl shadow-2xl shadow-primary/5 overflow-hidden min-h-[520px] ring-1 ring-black/5 dark:ring-white/5">
              {children}
            </div>
            {/* Mini cards para trocar rapidamente */}
            <div className="flex flex-wrap gap-2">
              {LAYERS.filter((l) => l.key !== activeLayer).map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => onLayerChange(key)}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-muted/60 hover:bg-muted border border-border/60 text-sm font-medium text-foreground transition-all duration-300 ease-out hover:scale-[1.02] hover:shadow-md"
                >
                  <Icon className="h-4 w-4 text-primary/80" strokeWidth={1.5} />
                  {label}
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Modo grade: cards bento com animação staggered */
          <div className="space-y-6">
            <div className="text-center">
              <p className="text-sm font-medium text-muted-foreground tracking-wide uppercase">Selecione uma camada</p>
              <h2 className="text-2xl font-semibold text-foreground mt-1 tracking-tight">Grade Bento</h2>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
              {LAYERS.map(({ key, label, desc, icon: Icon }, i) => (
                <button
                  key={key}
                  onClick={() => onLayerChange(key)}
                  className={cn(
                    "group relative flex flex-col items-center justify-center gap-5 p-8 lg:p-10 rounded-2xl",
                    "border border-border/60 bg-card/70 backdrop-blur-xl",
                    "transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]",
                    "hover:scale-[1.02] hover:shadow-2xl hover:shadow-primary/15 hover:border-primary/50 hover:-translate-y-1",
                    "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-background",
                    "animate-fluid-fade"
                  )}
                  style={{ animationDelay: `${i * 100}ms`, animationFillMode: "backwards" }}
                  aria-label={`Abrir ${label}`}
                >
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <div className="relative rounded-2xl p-5 bg-primary/10 group-hover:bg-primary/15 transition-all duration-300 group-hover:scale-105">
                    <Icon className="h-14 w-14 text-primary" strokeWidth={1.25} />
                  </div>
                  <div className="relative text-center space-y-1.5">
                    <p className="font-semibold text-foreground text-base lg:text-lg">{label}</p>
                    <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                  </div>
                  <span className="absolute bottom-5 right-5 flex items-center gap-1 text-xs text-muted-foreground/70 group-hover:text-primary transition-colors">
                    Abrir
                    <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
