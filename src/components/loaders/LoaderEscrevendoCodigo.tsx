/**
 * Loader 5 — "escrevendo seu código"
 * Uiverse typewriter (Nawsome) — máquina de escrever animada
 */
import { cn } from "@/lib/utils";

export interface LoaderEscrevendoCodigoProps {
  className?: string;
  message?: string;
  compact?: boolean;
}

export function LoaderEscrevendoCodigo({
  className,
  message = "Escrevendo seu código...",
  compact = false,
}: LoaderEscrevendoCodigoProps) {
  return (
    <div
      className={cn(
        compact
          ? "flex flex-row items-center justify-center gap-3 w-full min-h-[44px] px-4"
          : "flex flex-col items-center justify-center gap-4 rounded-2xl border border-white/10 bg-card/60 backdrop-blur-xl p-6",
        className
      )}
    >
      <div className={cn("showcase-typewriter", compact && "showcase-typewriter--compact")}>
        <div className="showcase-slide">
          <i />
        </div>
        <div className="showcase-paper" />
        <div className="showcase-keyboard" />
      </div>
      <p className={cn("font-medium text-foreground", compact ? "text-xs" : "text-sm")}>{message}</p>
    </div>
  );
}
