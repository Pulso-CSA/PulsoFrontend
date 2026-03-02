/**
 * PageLayout — Wrapper para páginas (Auth, Billing, Settings, etc.)
 * Aplica estilo conforme Layout A (futurista) ou B (clássico)
 */
import { useLayoutContext } from "@/contexts/LayoutContext";
import { cn } from "@/lib/utils";
import "@/styles/pulso-layouts.css";

interface PageLayoutProps {
  children: React.ReactNode;
  className?: string;
  /** centered = max-w estreito (Auth), full = largura total (Billing) */
  mode?: "centered" | "full";
}

export function PageLayout({ children, className, mode = "centered" }: PageLayoutProps) {
  const { layoutMode } = useLayoutContext();
  const isFuturistic = layoutMode === "A";

  return (
    <div
      className={cn(
        "min-h-[calc(100vh-3.5rem)] flex flex-col",
        mode === "centered" && "items-center justify-center",
        isFuturistic && "pulso-layout relative",
        className
      )}
    >
      {isFuturistic && (
        <div className="pulso-layout-ambient" aria-hidden>
          <div className="pulso-layout-orb pulso-layout-orb-1" />
          <div className="pulso-layout-orb pulso-layout-orb-2" />
          <div className="pulso-layout-orb pulso-layout-orb-3" />
        </div>
      )}
      <div
        className={cn(
          "relative z-10 w-full mx-auto px-6 py-8",
          mode === "centered" && "max-w-[500px]",
          mode === "full" && "max-w-[1400px]",
          mode === "centered" && (isFuturistic
            ? "rounded-2xl border border-white/10 bg-card/60 backdrop-blur-xl shadow-2xl"
            : "rounded-xl border border-border bg-card shadow-sm")
        )}
      >
        {children}
      </div>
    </div>
  );
}
