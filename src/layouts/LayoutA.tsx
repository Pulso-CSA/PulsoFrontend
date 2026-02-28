/**
 * Layout A — Sidebar futurista e elegante
 * 4 serviços fixos no topo, UserSidebar no canto inferior esquerdo
 * Paleta Pulso: #222023, #420d95, #a54bce, #60bcd5, #1897a0
 */
import { Workflow, CloudCog, TrendingDown, Brain, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import "@/styles/pulso-layouts.css";

export type ServiceKey = "pulso" | "cloud" | "finops" | "data";

const SERVICES: { key: ServiceKey; label: string; icon: LucideIcon }[] = [
  { key: "pulso", label: "Pulso CSA", icon: Workflow },
  { key: "cloud", label: "Cloud IaC", icon: CloudCog },
  { key: "finops", label: "FinOps", icon: TrendingDown },
  { key: "data", label: "Dados & IA", icon: Brain },
];

interface LayoutAProps {
  activeService: ServiceKey | null;
  onServiceChange: (key: ServiceKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

export function LayoutA({ activeService, onServiceChange, children, className }: LayoutAProps) {
  return (
    <div className={cn("pulso-layout pulso-layout-a", className)}>
      {/* Barra de serviços fixa no topo */}
      <div className="pulso-layout-a-services-bar flex-shrink-0" aria-label="Serviços">
        <div className="pulso-layout-a-services-inner">
          {SERVICES.map(({ key, label, icon: Icon }) => {
            const isActive = activeService === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => onServiceChange(isActive ? null : key)}
                className={cn("pulso-layout-a-btn pulso-layout-a-btn-horizontal", isActive && "pulso-active")}
                title={label}
                aria-pressed={isActive}
                aria-label={`${label} ${isActive ? "ativo" : "inativo"}`}
              >
                <Icon className="h-5 w-5" strokeWidth={1.5} />
                <span className="text-xs font-medium truncate">{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Área inferior: conteúdo (sidebar conta/tema/layout fica no AppShell) */}
      <div className="pulso-layout-a-body flex-1 flex min-h-0">
        {/* Área principal centralizada */}
        <main className="pulso-layout-a-main flex-1 bg-background/50 w-full">
          <div className="pulso-layout-a-content">{children}</div>
        </main>
      </div>
    </div>
  );
}
