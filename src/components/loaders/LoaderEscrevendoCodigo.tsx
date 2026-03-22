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
  if (compact) {
    return (
      <div className={cn("flex flex-row items-center gap-3 w-full min-h-[44px] px-2", className)}>
        <div className="w-[56px] h-[36px] shrink-0 flex items-center" aria-hidden>
          <div className="showcase-typewriter showcase-typewriter--compact">
            <div className="showcase-slide">
              <i />
            </div>
            <div className="showcase-paper" />
            <div className="showcase-keyboard" />
          </div>
        </div>
        <p className="text-xs font-medium text-foreground/90 truncate">{message}</p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-2xl border border-white/10 bg-card/60 backdrop-blur-xl p-6",
        className
      )}
    >
      <div className="showcase-typewriter">
        <div className="showcase-slide">
          <i />
        </div>
        <div className="showcase-paper" />
        <div className="showcase-keyboard" />
      </div>
      <p className="font-medium text-foreground text-sm">{message}</p>
    </div>
  );
}
