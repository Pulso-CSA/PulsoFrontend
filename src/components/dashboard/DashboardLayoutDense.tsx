/**
 * Layout Denso — estilo da imagem
 * Cards com bordas em gradiente brilhante, fundo escuro
 */
import { cn } from "@/lib/utils";
import { LAYER_CONFIG, type LayerKey } from "./LayerCard";

interface DashboardLayoutDenseProps {
  activeLayer: LayerKey | null;
  onLayerChange: (layer: LayerKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

const BORDER_GLOW: Record<LayerKey, { active: string; inactive: string }> = {
  pulso: {
    active: "shadow-[0_0_30px_-5px_rgba(249,115,22,0.6),0_0_20px_-5px_rgba(236,72,153,0.5)]",
    inactive: "shadow-[0_0_15px_-5px_rgba(139,92,246,0.4),0_0_10px_-5px_rgba(59,130,246,0.3)]",
  },
  cloud: {
    active: "shadow-[0_0_30px_-5px_rgba(249,115,22,0.6),0_0_20px_-5px_rgba(236,72,153,0.5)]",
    inactive: "shadow-[0_0_15px_-5px_rgba(139,92,246,0.4),0_0_10px_-5px_rgba(99,102,241,0.3)]",
  },
  finops: {
    active: "shadow-[0_0_30px_-5px_rgba(249,115,22,0.6),0_0_20px_-5px_rgba(236,72,153,0.5)]",
    inactive: "shadow-[0_0_15px_-5px_rgba(34,211,238,0.4),0_0_10px_-5px_rgba(34,197,94,0.3)]",
  },
  data: {
    active: "shadow-[0_0_30px_-5px_rgba(249,115,22,0.6),0_0_20px_-5px_rgba(236,72,153,0.5)]",
    inactive: "shadow-[0_0_15px_-5px_rgba(34,211,238,0.4),0_0_10px_-5px_rgba(250,204,21,0.3)]",
  },
};

const BORDER_GRADIENT: Record<LayerKey, { active: string; inactive: string }> = {
  pulso: {
    active: "from-orange-500 via-pink-500 to-fuchsia-500",
    inactive: "from-violet-600 via-purple-500 to-blue-500",
  },
  cloud: {
    active: "from-orange-500 via-pink-500 to-fuchsia-500",
    inactive: "from-violet-600 via-indigo-500 to-blue-500",
  },
  finops: {
    active: "from-orange-500 via-pink-500 to-fuchsia-500",
    inactive: "from-cyan-500 via-teal-500 to-emerald-500",
  },
  data: {
    active: "from-orange-500 via-pink-500 to-fuchsia-500",
    inactive: "from-cyan-500 via-sky-500 to-amber-400",
  },
};

function DenseCard({
  layer,
  isActive,
  onClick,
}: {
  layer: (typeof LAYER_CONFIG)[number];
  isActive: boolean;
  onClick: () => void;
}) {
  const { key, label, desc, icon: Icon } = layer;
  const glow = BORDER_GLOW[key];
  const gradient = BORDER_GRADIENT[key];

  return (
    <button
      onClick={onClick}
      className={cn(
        "group relative flex flex-col items-center rounded-xl min-w-[200px] transition-all duration-300 p-[2px]",
        isActive ? glow.active : cn(glow.inactive, "hover:shadow-[0_0_25px_-5px_rgba(249,115,22,0.4)]")
      )}
    >
      {/* Borda em gradiente — wrapper */}
      <div
        className={cn(
          "w-full h-full rounded-xl bg-gradient-to-b p-[2px]",
          isActive ? gradient.active : gradient.inactive
        )}
      >
        {/* Interior escuro */}
        <div className="w-full h-full rounded-[10px] bg-black flex flex-col items-center justify-center p-5">
          <div className="p-2.5 rounded-lg bg-white/10 mb-3">
            <Icon className="h-7 w-7 text-white" strokeWidth={1.5} />
          </div>
          <h3 className="font-bold text-white text-sm">{label}</h3>
          <p className="text-xs text-white/70 mt-0.5">{desc}</p>
        </div>
      </div>
    </button>
  );
}

export function DashboardLayoutDense({
  activeLayer,
  onLayerChange,
  children,
  className,
}: DashboardLayoutDenseProps) {
  return (
    <div className={cn("flex flex-col min-h-[calc(100vh-4rem)]", className)}>
      {/* Barra de cards com glow */}
      <div className="shrink-0 px-4 py-4 bg-black/80 border-b border-white/5">
        <div className="flex flex-wrap justify-center gap-4 max-w-4xl mx-auto">
          {LAYER_CONFIG.map((layer) => (
            <DenseCard
              key={layer.key}
              layer={layer}
              isActive={activeLayer === layer.key}
              onClick={() => onLayerChange(activeLayer === layer.key ? null : layer.key)}
            />
          ))}
        </div>
      </div>

      <main className="flex-1 overflow-auto min-w-0 bg-background">
        {children}
      </main>
    </div>
  );
}
