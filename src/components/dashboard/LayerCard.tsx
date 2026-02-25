/**
 * Card de camada — glassmorphism
 */
import { Workflow, CloudCog, TrendingDown, Brain, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type LayerKey = "pulso" | "cloud" | "finops" | "data";

export const LAYER_CONFIG: {
  key: LayerKey;
  label: string;
  desc: string;
  icon: LucideIcon;
  color: "primary" | "info" | "finops" | "dataAi";
}[] = [
  { key: "pulso", label: "Pulso CSA", desc: "Blueprint & Estrutura", icon: Workflow, color: "primary" },
  { key: "cloud", label: "Cloud IaC", desc: "AWS, Azure, GCP", icon: CloudCog, color: "info" },
  { key: "finops", label: "FinOps", desc: "Otimização de custos", icon: TrendingDown, color: "finops" },
  { key: "data", label: "Dados & IA", desc: "Analytics e modelos", icon: Brain, color: "dataAi" },
];

interface LayerCardProps {
  layer: (typeof LAYER_CONFIG)[number];
  isActive: boolean;
  onClick: () => void;
  variant?: "default" | "compact" | "minimal";
  className?: string;
}

const gradientByColor: Record<string, string> = {
  primary: "from-primary/30 via-primary/15 to-secondary/25",
  info: "from-info/30 via-info/15 to-secondary/25",
  finops: "from-finops/30 via-finops/15 to-secondary/25",
  dataAi: "from-dataAi/30 via-dataAi/15 to-secondary/25",
};

export function LayerCard({ layer, isActive, onClick, variant = "default", className }: LayerCardProps) {
  const { icon: Icon, label, desc, color } = layer;
  const gradient = gradientByColor[color];

  const glass = "border border-white/10 bg-white/5 backdrop-blur-xl rounded-2xl transition-all duration-300";

  if (variant === "compact") {
    return (
      <button
        onClick={onClick}
        className={cn(
          glass,
          "flex items-center gap-4 p-4 text-left",
          isActive ? "ring-2 ring-primary/50 bg-primary/10" : "hover:bg-white/10 hover:border-white/20",
          className
        )}
        aria-pressed={isActive}
        aria-label={`${label} ${isActive ? "ativo" : "inativo"}`}
      >
        <div className={cn("p-2.5 rounded-xl", isActive ? "bg-primary/20" : "bg-white/10")}>
          <Icon className={cn("h-5 w-5", isActive ? "text-primary" : "text-foreground/80")} strokeWidth={1.5} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-foreground text-sm truncate">{label}</p>
          <p className="text-xs text-muted-foreground truncate">{desc}</p>
        </div>
      </button>
    );
  }

  if (variant === "minimal") {
    return (
      <button
        onClick={onClick}
        className={cn(
          glass,
          "flex flex-col items-center justify-center gap-4 p-6 text-center",
          isActive ? "ring-2 ring-primary/50 bg-primary/10" : "hover:bg-white/10 hover:border-white/20",
          className
        )}
        aria-pressed={isActive}
        aria-label={`${label} ${isActive ? "ativo" : "inativo"}`}
      >
        <div className={cn("p-4 rounded-2xl bg-gradient-to-b", gradient)}>
          <Icon className="h-8 w-8 text-white" strokeWidth={1.5} />
        </div>
        <div>
          <p className="font-semibold text-foreground">{label}</p>
          <p className="text-sm text-muted-foreground mt-0.5">{desc}</p>
        </div>
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        glass,
        "flex flex-col items-center justify-center gap-4 p-6 text-center",
        isActive ? "ring-2 ring-primary/50 bg-primary/10" : "hover:bg-white/10 hover:border-white/20",
        className
      )}
      aria-pressed={isActive}
      aria-label={`${label} ${isActive ? "ativo" : "inativo"}`}
    >
      <div className={cn("p-3 rounded-xl bg-gradient-to-b", gradient)}>
        <Icon className="h-7 w-7 text-white" strokeWidth={1.5} />
      </div>
      <div>
        <p className="font-medium text-foreground truncate">{label}</p>
        <p className="text-xs text-muted-foreground truncate mt-0.5">{desc}</p>
      </div>
    </button>
  );
}
