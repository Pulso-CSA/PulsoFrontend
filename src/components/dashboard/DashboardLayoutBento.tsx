/**
 * Layout Bento — carrossel circular ao longo do semicírculo (sentido horário)
 * Scroll/rotação move o foco no sentido horário; efeito de fade nos itens
 */
import { useState, useRef, useCallback } from "react";
import { X, ChevronRight, ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { LAYER_CONFIG, type LayerKey } from "./LayerCard";

interface DashboardLayoutBentoProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const N = LAYER_CONFIG.length;

/** Ângulos ao longo do arco (180° → 0°, sentido horário: esquerda → topo → direita) */
const ANGLES = [180, 120, 60, 0];

function getCircularDistance(i: number, focused: number): number {
  const d = Math.abs(i - focused);
  return Math.min(d, N - d);
}

function getPositionOnArc(angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180;
  const x = Math.cos(rad);
  const y = -Math.sin(rad);
  return { x, y };
}

/** Semicírculo central com gradiente e glow — define o caminho do carrossel */
function SemicirclePath() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none" aria-hidden>
      <svg
        viewBox="0 0 400 220"
        className="w-full max-w-[min(95vw,480px)] h-auto"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="bento-arc-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.95} />
            <stop offset="50%" stopColor="#8b5cf6" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#ec4899" stopOpacity={0.95} />
          </linearGradient>
          <filter id="bento-arc-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <path
          d="M 20 110 A 180 180 0 0 1 380 110"
          fill="none"
          stroke="url(#bento-arc-grad)"
          strokeWidth="2.5"
          filter="url(#bento-arc-glow)"
        />
      </svg>
    </div>
  );
}

export function DashboardLayoutBento({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutBentoProps) {
  const others = LAYER_CONFIG.filter((l) => l.key !== "pulso");
  const [focusedIndex, setFocusedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const wheelAccum = useRef(0);

  const goNext = useCallback(() => {
    setFocusedIndex((i) => (i + 1) % N);
  }, []);

  const goPrev = useCallback(() => {
    setFocusedIndex((i) => (i - 1 + N) % N);
  }, []);

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      wheelAccum.current += e.deltaY;
      const threshold = 50;
      if (wheelAccum.current > threshold) {
        wheelAccum.current = 0;
        goNext();
        e.preventDefault();
      } else if (wheelAccum.current < -threshold) {
        wheelAccum.current = 0;
        goPrev();
        e.preventDefault();
      }
    },
    [goNext, goPrev]
  );

  return (
    <div
      className={cn(
        "min-h-[calc(100vh-4rem)] relative bg-[#0a0a0f] p-4 lg:p-6 overflow-hidden",
        className
      )}
    >
      <div className="relative z-10 max-w-6xl mx-auto">
        {activeLayer ? (
          <div className="space-y-4 animate-fluid-fade">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {(() => {
                  const layer = LAYER_CONFIG.find((l) => l.key === activeLayer);
                  const Icon = layer?.icon;
                  return Icon ? (
                    <div className="p-2 rounded-xl bg-white/5 border border-white/10 bg-gradient-to-br from-white/10 to-transparent">
                      <Icon className="h-5 w-5 text-primary" strokeWidth={1.5} />
                    </div>
                  ) : null;
                })()}
                <div>
                  <h2 className="text-base font-semibold text-white">
                    {LAYER_CONFIG.find((l) => l.key === activeLayer)?.label}
                  </h2>
                  <p className="text-xs text-white/60">
                    {LAYER_CONFIG.find((l) => l.key === activeLayer)?.desc}
                  </p>
                </div>
              </div>
              <button
                onClick={() => onLayerChange(null)}
                className="p-2 rounded-xl text-white/60 hover:text-white hover:bg-white/10 border border-transparent hover:border-white/10 transition-colors"
                aria-label="Voltar"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl overflow-hidden min-h-[480px] shadow-[0_0_40px_-10px_rgba(59,130,246,0.15),0_0_25px_-8px_rgba(139,92,246,0.1)]">
              {children}
            </div>
            <div className="flex flex-wrap gap-2">
              {others.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => onLayerChange(key)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 text-white/80 hover:text-white transition-all"
                >
                  <Icon className="h-3.5 w-3.5" strokeWidth={1.5} />
                  {label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div
            ref={containerRef}
            onWheel={handleWheel}
            className="relative min-h-[420px] flex items-center justify-center select-none"
          >
            <div className="relative w-full max-w-[480px] aspect-[400/220]" style={{ minHeight: 260 }}>
              <SemicirclePath />

              {/* Módulos posicionados ao longo do arco — efeito de fade baseado na distância circular */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative w-full h-full" style={{ paddingTop: "18%" }}>
                  {LAYER_CONFIG.map((layer, i) => {
                    const Icon = layer.icon;
                    const distance = getCircularDistance(i, focusedIndex);
                    const opacity = distance === 0 ? 1 : distance === 1 ? 0.5 : 0.2;
                    const scale = distance === 0 ? 1 : 0.88;
                    const isFocused = focusedIndex === i;

                    const { x, y } = getPositionOnArc(ANGLES[i]);
                    const left = 50 + x * 48;
                    const top = 50 + y * 48;
                    const rotate = -ANGLES[i] + 90;

                    return (
                      <button
                        key={layer.key}
                        onClick={() => onLayerChange(layer.key)}
                        className={cn(
                          "group absolute flex flex-col items-center gap-2 p-3 rounded-2xl -translate-x-1/2 -translate-y-1/2",
                          "bg-black/60 backdrop-blur-xl border transition-all duration-300",
                          isFocused
                            ? "border-violet-500/50 shadow-[0_0_30px_-8px_rgba(139,92,246,0.5)]"
                            : "border-white/10 hover:border-white/20 hover:bg-white/5"
                        )}
                        style={{
                          left: `${left}%`,
                          top: `${top}%`,
                          transform: `translate(-50%, -50%) rotate(${rotate}deg) scale(${scale})`,
                          opacity,
                          width: 100,
                        }}
                        aria-label={layer.label}
                        aria-current={isFocused ? "true" : undefined}
                      >
                        <div
                          className={cn(
                            "p-2.5 rounded-xl shrink-0 transition-colors",
                            isFocused ? "bg-blue-500/25" : "bg-white/10 group-hover:bg-blue-500/15"
                          )}
                        >
                          <Icon
                            className={cn("h-5 w-5", isFocused ? "text-white" : "text-white/70")}
                            strokeWidth={1.5}
                          />
                        </div>
                        <div className="text-center">
                          <p className={cn("font-medium text-xs truncate w-full", isFocused ? "text-white" : "text-white/80")}>
                            {layer.label}
                          </p>
                          <p className="text-[10px] text-white/50 truncate w-full hidden sm:block">{layer.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Botões de navegação — sentido horário (direita) e anti-horário (esquerda) */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4">
              <button
                onClick={goPrev}
                className="p-2.5 rounded-xl text-white/60 hover:text-white hover:bg-white/10 border border-white/10 transition-colors"
                aria-label="Anterior (anti-horário)"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <span className="text-xs text-white/40 tabular-nums">
                {focusedIndex + 1} / {N}
              </span>
              <button
                onClick={goNext}
                className="p-2.5 rounded-xl text-white/60 hover:text-white hover:bg-white/10 border border-white/10 transition-colors"
                aria-label="Próximo (sentido horário)"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>

            <p className="absolute bottom-12 left-1/2 -translate-x-1/2 text-xs text-white/40 text-center">
              Role a roda do mouse ou use as setas para navegar no sentido horário
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
