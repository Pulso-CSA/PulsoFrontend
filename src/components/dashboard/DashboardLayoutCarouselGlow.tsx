/**
 * Layout Carousel Glow — inspirado na imagem
 * Cards escuros com glow interno (magenta → azul), jogo de luzes
 */
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { LAYER_CONFIG, type LayerKey } from "./LayerCard";

interface DashboardLayoutCarouselGlowProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const GLOW_GRADIENT: Record<LayerKey, { top: string; glow: string }> = {
  pulso: { top: "from-indigo-950/95", glow: "from-fuchsia-500/50 via-violet-500/40 to-blue-500/50" },
  cloud: { top: "from-violet-950/95", glow: "from-pink-500/50 via-purple-500/40 to-indigo-500/50" },
  finops: { top: "from-purple-950/95", glow: "from-rose-500/50 via-fuchsia-500/40 to-violet-500/50" },
  data: { top: "from-fuchsia-950/95", glow: "from-violet-500/50 via-indigo-500/40 to-blue-500/50" },
};

function GlowCard({
  layer,
  isActive,
  onClick,
}: {
  layer: (typeof LAYER_CONFIG)[number];
  isActive: boolean;
  onClick: () => void;
}) {
  const { key, label, desc, icon: Icon } = layer;
  const { top, glow } = GLOW_GRADIENT[key];

  return (
    <button
      onClick={onClick}
      className={cn(
        "group relative flex flex-col items-center text-left rounded-2xl overflow-hidden transition-all duration-500",
        "min-w-[260px] max-w-[280px] p-6 pb-8",
        isActive
          ? "scale-105 carousel-glow-card carousel-glow-card-active"
          : "hover:scale-[1.02] carousel-glow-card"
      )}
    >
      {/* Fundo escuro */}
      <div className={cn("absolute inset-0 bg-gradient-to-b", top, "to-transparent")} />

      {/* Glow interno — parte inferior, magenta → azul */}
      <div
        className={cn(
          "absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t",
          glow
        )}
        style={{
          filter: "blur(32px)",
          opacity: 0.9,
          maskImage: "linear-gradient(to top, black 20%, transparent 80%)",
          WebkitMaskImage: "linear-gradient(to top, black 20%, transparent 80%)",
        }}
      />

      {/* Brilho nas bordas */}
      <div
        className="absolute inset-0 rounded-2xl opacity-40"
        style={{
          background: "linear-gradient(180deg, transparent 40%, rgba(168,85,247,0.15) 70%, rgba(99,102,241,0.2) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Conteúdo */}
      <div className="relative z-10 flex flex-col items-center text-center w-full">
        <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center mb-4 ring-2 ring-white/5">
          <Icon className="h-6 w-6 text-white" strokeWidth={1.5} />
        </div>
        <h3 className="font-bold text-white text-base mb-2">{label}</h3>
        <p className="text-sm text-white/80 leading-relaxed mb-5 max-w-[220px]">{desc}</p>
        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-white/90 group-hover:text-white transition-colors">
          Saiba mais
          <ChevronRight className="h-4 w-4" strokeWidth={2} />
        </span>
      </div>
    </button>
  );
}

export function DashboardLayoutCarouselGlow({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutCarouselGlowProps) {
  return (
    <div className={cn("min-h-[calc(100vh-4rem)] flex flex-col p-6", className)}>
      {activeLayer ? (
        <div className="flex-1 max-w-5xl mx-auto w-full space-y-8 animate-fluid-fade">
          {/* Área de conteúdo com glow */}
          <div className="relative rounded-2xl overflow-hidden min-h-[520px]">
            {/* Glow de fundo do container */}
            <div
              className="absolute inset-0 opacity-30"
              style={{
                background: "linear-gradient(135deg, rgba(168,85,247,0.15) 0%, rgba(99,102,241,0.1) 50%, rgba(236,72,153,0.1) 100%)",
                filter: "blur(60px)",
              }}
            />
            <div className="relative rounded-2xl border border-white/10 bg-card/95 backdrop-blur-sm min-h-[520px] overflow-hidden">
              {children}
            </div>
          </div>

          {/* Cards de navegação com glow */}
          <div className="flex flex-wrap justify-center gap-6">
            {LAYER_CONFIG.map((layer) => (
              <GlowCard
                key={layer.key}
                layer={layer}
                isActive={activeLayer === layer.key}
                onClick={() => onLayerChange(activeLayer === layer.key ? null : layer.key)}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="flex flex-wrap justify-center gap-8 max-w-5xl">
            {LAYER_CONFIG.map((layer) => (
              <GlowCard
                key={layer.key}
                layer={layer}
                isActive={false}
                onClick={() => onLayerChange(layer.key)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
