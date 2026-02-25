/**
 * Layout Carrossel Glass — inspirado na imagem
 * Card central em destaque, laterais parcialmente visíveis, glassmorphism
 */
import { useState } from "react";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { LAYER_CONFIG, type LayerKey } from "./LayerCard";

interface DashboardLayoutCarouselGlassProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const CARD_GRADIENTS: Record<LayerKey, { bg: string; orb: string }> = {
  pulso: { bg: "from-blue-600/40 via-cyan-500/30 to-indigo-600/40", orb: "from-cyan-500/30" },
  cloud: { bg: "from-indigo-600/40 via-violet-500/30 to-purple-600/40", orb: "from-violet-500/30" },
  finops: { bg: "from-purple-600/40 via-fuchsia-500/30 to-pink-600/40", orb: "from-fuchsia-500/30" },
  data: { bg: "from-pink-600/40 via-rose-500/30 to-fuchsia-600/40", orb: "from-rose-500/30" },
};

export function DashboardLayoutCarouselGlass({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutCarouselGlassProps) {
  const [focusedIndex, setFocusedIndex] = useState(0);
  const currentIndex = activeLayer ? LAYER_CONFIG.findIndex((l) => l.key === activeLayer) : focusedIndex;

  const goPrev = () => {
    const idx = currentIndex <= 0 ? LAYER_CONFIG.length - 1 : currentIndex - 1;
    if (activeLayer) onLayerChange(LAYER_CONFIG[idx].key);
    else setFocusedIndex(idx);
  };

  const goNext = () => {
    const idx = currentIndex >= LAYER_CONFIG.length - 1 ? 0 : currentIndex + 1;
    if (activeLayer) onLayerChange(LAYER_CONFIG[idx].key);
    else setFocusedIndex(idx);
  };

  const getCardIndex = (offset: number) => {
    const len = LAYER_CONFIG.length;
    return ((currentIndex + offset) % len + len) % len;
  };

  return (
    <div className={cn("min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-4 lg:p-8", className)}>
      {activeLayer ? (
        <div className="w-full max-w-4xl mx-auto space-y-6 animate-fluid-fade">
          <div className="flex items-center justify-between">
            <button onClick={goPrev} className="p-2 rounded-full text-white/70 hover:text-white hover:bg-white/10 transition-colors" aria-label="Anterior">
              <ChevronLeft className="h-6 w-6" />
            </button>
            <h2 className="text-lg font-semibold text-white">
              {LAYER_CONFIG.find((l) => l.key === activeLayer)?.label}
            </h2>
            <button onClick={goNext} className="p-2 rounded-full text-white/70 hover:text-white hover:bg-white/10 transition-colors" aria-label="Próximo">
              <ChevronRight className="h-6 w-6" />
            </button>
          </div>
          <div className="rounded-3xl border border-white/20 overflow-hidden min-h-[500px] bg-white/5 backdrop-blur-2xl shadow-[0_0_50px_-15px_rgba(34,211,238,0.2),0_0_30px_-10px_rgba(139,92,246,0.15)]">
            {children}
          </div>
          <button onClick={() => onLayerChange(null)} className="text-sm text-white/60 hover:text-white">
            Voltar à seleção
          </button>
        </div>
      ) : (
        <div className="w-full max-w-3xl mx-auto">
          {/* Orbes de fundo — jogo de luzes */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-1/2 left-1/4 w-72 h-72 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-500/25 blur-[100px] animate-soft-glow" />
            <div className="absolute top-1/2 right-1/4 w-72 h-72 translate-x-1/2 -translate-y-1/2 rounded-full bg-violet-500/25 blur-[100px] animate-soft-glow" style={{ animationDelay: "1s" }} />
            <div className="absolute top-1/3 right-1/3 w-48 h-48 rounded-full bg-fuchsia-500/15 blur-[80px] animate-soft-glow" style={{ animationDelay: "1.5s" }} />
          </div>

          {/* Carrossel: 3 cards visíveis, central em destaque */}
          <div className="relative flex items-center justify-center w-full overflow-hidden">
            <div className="flex items-center justify-center">
              {/* Card esquerdo (peek) */}
              <button
                onClick={goPrev}
                className={cn(
                  "relative flex-shrink-0 w-[120px] lg:w-[160px] h-[300px] rounded-2xl overflow-hidden -mr-8 lg:-mr-12",
                  "border border-white/10 bg-white/5 backdrop-blur-xl",
                  "transition-all duration-500 hover:scale-[1.03] hover:opacity-95 hover:z-20"
                )}
              >
                <div className={cn("absolute inset-0 bg-gradient-to-b", CARD_GRADIENTS[LAYER_CONFIG[getCardIndex(-1)].key].bg)} />
                <div className="absolute inset-0 flex items-center justify-center">
                  {(() => {
                    const layer = LAYER_CONFIG[getCardIndex(-1)];
                    const Icon = layer.icon;
                    return <Icon className="h-16 w-16 text-white/80" strokeWidth={1} />;
                  })()}
                </div>
              </button>

              {/* Card central */}
              <button
                onClick={() => onLayerChange(LAYER_CONFIG[currentIndex].key)}
                className={cn(
                  "relative flex-shrink-0 w-[280px] lg:w-[360px] min-h-[340px] rounded-3xl overflow-hidden z-10",
                  "border-2 border-white/20 bg-white/10 backdrop-blur-2xl shadow-2xl",
                  "transition-all duration-500"
                )}
              >
                <div className={cn("absolute inset-0 bg-gradient-to-b", CARD_GRADIENTS[LAYER_CONFIG[currentIndex].key].bg)} />
                <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center">
                  <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center mb-5 ring-4 ring-white/10">
                    {(() => {
                      const Icon = LAYER_CONFIG[currentIndex].icon;
                      return <Icon className="h-7 w-7 text-white" strokeWidth={1.5} />;
                    })()}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">
                    {LAYER_CONFIG[currentIndex].label}
                  </h3>
                  <p className="text-sm text-white/80 mb-8 max-w-[280px] leading-relaxed">
                    {LAYER_CONFIG[currentIndex].desc}
                  </p>
                  <div className="flex gap-8">
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); goPrev(); }}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-colors"
                    >
                      <Check className="h-4 w-4" />
                      Voltar
                    </button>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); goNext(); }}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-colors"
                    >
                      <Check className="h-4 w-4" />
                      Pular
                    </button>
                  </div>
                </div>
              </button>

              {/* Card direito (peek) */}
              <button
                onClick={goNext}
                className={cn(
                  "relative flex-shrink-0 w-[120px] lg:w-[160px] h-[300px] rounded-2xl overflow-hidden -ml-8 lg:-ml-12",
                  "border border-white/10 bg-white/5 backdrop-blur-xl",
                  "transition-all duration-500 hover:scale-[1.03] hover:opacity-95 hover:z-20"
                )}
              >
                <div className={cn("absolute inset-0 bg-gradient-to-b", CARD_GRADIENTS[LAYER_CONFIG[getCardIndex(1)].key].bg)} />
                <div className="absolute inset-0 flex items-center justify-center">
                  {(() => {
                    const layer = LAYER_CONFIG[getCardIndex(1)];
                    const Icon = layer.icon;
                    return <Icon className="h-16 w-16 text-white/80" strokeWidth={1} />;
                  })()}
                </div>
              </button>
            </div>
          </div>

          {/* Indicadores */}
          <div className="flex justify-center gap-2 mt-10">
            <button onClick={goPrev} className="p-2 rounded-full text-white/50 hover:text-white hover:bg-white/10" aria-label="Anterior">
              <ChevronLeft className="h-5 w-5" />
            </button>
            {LAYER_CONFIG.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setFocusedIndex(idx)}
                className={cn("rounded-full transition-all", idx === currentIndex ? "w-8 h-2 bg-white" : "w-2 h-2 bg-white/40 hover:bg-white/60")}
                aria-label={`Slide ${idx + 1}`}
              />
            ))}
            <button onClick={goNext} className="p-2 rounded-full text-white/50 hover:text-white hover:bg-white/10" aria-label="Próximo">
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
