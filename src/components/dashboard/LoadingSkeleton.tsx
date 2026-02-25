/**
 * LoadingSkeleton – Indicador de carregamento durante treino ou previsão
 * Baseado no PulsoAPI frontend (variantes chat, metrics, charts)
 */

import { cn } from "@/lib/utils";

export interface LoadingSkeletonProps {
  message?: string;
  variant?: "chat" | "metrics" | "charts";
  className?: string;
}

export function LoadingSkeleton({
  message = "Processando...",
  variant = "chat",
  className,
}: LoadingSkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/5 bg-chat-system/90 p-5 shadow-md animate-pulse",
        className
      )}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="flex gap-1.5 items-end h-4">
          <div className="w-2 h-2 rounded-full animate-typing-bounce bg-primary" style={{ animationDelay: "0ms" }} />
          <div className="w-2 h-2 rounded-full animate-typing-bounce bg-primary" style={{ animationDelay: "200ms" }} />
          <div className="w-2 h-2 rounded-full animate-typing-bounce bg-primary" style={{ animationDelay: "400ms" }} />
        </div>
        <span className="text-sm text-muted-foreground">{message}</span>
      </div>
      <div className="space-y-3">
        <div className="h-3 rounded bg-white/10 w-4/5" />
        <div className="h-3 rounded bg-white/10 w-3/5" />
      </div>
      {variant === "metrics" && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 rounded-lg bg-white/10" />
          ))}
        </div>
      )}
      {variant === "charts" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 rounded-xl bg-white/10" />
          ))}
        </div>
      )}
    </div>
  );
}
