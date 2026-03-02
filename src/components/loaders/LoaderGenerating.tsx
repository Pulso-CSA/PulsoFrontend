/**
 * Elemento 1 — Loader Generating (anel rotativo)
 * Sem texto, centralizado, tamanho proporcional ao chat, atrás do glass
 */
import { cn } from "@/lib/utils";

export interface LoaderGeneratingProps {
  className?: string;
}

export function LoaderGenerating({ className }: LoaderGeneratingProps) {
  return (
    <div
      className={cn(
        "showcase-loader1-bg showcase-loader1-bg--chat",
        "absolute inset-0 flex items-center justify-center pointer-events-none",
        className
      )}
      aria-hidden
    >
      <div className="showcase-loader1" />
    </div>
  );
}
