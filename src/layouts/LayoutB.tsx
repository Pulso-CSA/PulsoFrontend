/**
 * Layout B — Carrossel futurista e elegante
 * 4 serviços fixos no topo, UserSidebar no canto inferior esquerdo
 * Paleta Pulso: #222023, #420d95, #a54bce, #60bcd5, #1897a0
 */
import { Workflow, CloudCog, TrendingDown, Brain } from "lucide-react";
import { cn } from "@/lib/utils";
import "@/styles/pulso-layouts.css";

export type ServiceKey = "pulso" | "cloud" | "finops" | "data";

const SERVICES: { key: ServiceKey; label: string; desc: string; icon: typeof Workflow }[] = [
  { key: "pulso", label: "Pulso CSA", desc: "Blueprint & Estrutura", icon: Workflow },
  { key: "cloud", label: "Cloud IaC", desc: "AWS, Azure, GCP", icon: CloudCog },
  { key: "finops", label: "FinOps", desc: "Otimização de custos", icon: TrendingDown },
  { key: "data", label: "Dados & IA", desc: "Analytics e modelos", icon: Brain },
];

interface LayoutBProps {
  activeService: ServiceKey | null;
  onServiceChange: (key: ServiceKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

export function LayoutB({ activeService, onServiceChange, children, className }: LayoutBProps) {
  return (
    <div className={cn("pulso-layout pulso-layout-b", className)}>
      {/* 4 serviços fixos no topo */}
      <div className="pulso-layout-b-carousel flex-shrink-0">
        <div className="pulso-layout-b-carousel-inner">
          {SERVICES.map(({ key, label, desc, icon: Icon }) => {
            const isActive = activeService === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => onServiceChange(isActive ? null : key)}
                className={cn("pulso-layout-b-card", isActive && "pulso-active")}
                aria-pressed={isActive}
                aria-label={`${label} ${isActive ? "ativo" : "inativo"}`}
              >
                <div className="pulso-layout-b-card-icon">
                  <Icon
                    className={cn("h-6 w-6", isActive ? "text-primary" : "text-muted-foreground")}
                    strokeWidth={1.5}
                  />
                </div>
                <p className="font-semibold text-sm text-foreground mb-0.5">{label}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Área inferior: conteúdo (sidebar conta/tema/layout fica no AppShell) */}
      <div className="pulso-layout-b-body flex-1 flex min-h-0">
        {/* Área principal centralizada */}
        <main className="pulso-layout-b-main flex-1 bg-background/50 w-full">
          <div className="pulso-layout-b-content">{children}</div>
        </main>
      </div>
    </div>
  );
}
