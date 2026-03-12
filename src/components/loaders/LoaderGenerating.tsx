/**
 * Sequência de carregamento para chats:
 * 1) Loader 4 (livro) -> "estudando sua requisição"
 * 2) Loader 5 (máquina) -> "escrevendo sua resposta"
 */
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { LoaderEstudandoArquivos } from "./LoaderEstudandoArquivos";
import { LoaderEscrevendoCodigo } from "./LoaderEscrevendoCodigo";

export interface LoaderGeneratingProps {
  className?: string;
  firstPhaseMs?: number;
}

export function LoaderGenerating({ className, firstPhaseMs = 2200 }: LoaderGeneratingProps) {
  const [phase, setPhase] = useState<"studying" | "writing">("studying");

  useEffect(() => {
    setPhase("studying");
    const timer = window.setTimeout(() => setPhase("writing"), firstPhaseMs);
    return () => window.clearTimeout(timer);
  }, [firstPhaseMs]);

  return (
    <div className={cn("flex justify-start", className)}>
      <div className="rounded-2xl px-4 py-3 bg-chat-system border border-white/5 text-sm text-muted-foreground">
        {phase === "studying" ? (
          <LoaderEstudandoArquivos compact message="Estudando sua requisição..." />
        ) : (
          <LoaderEscrevendoCodigo compact message="Escrevendo sua resposta..." />
        )}
      </div>
    </div>
  );
}
