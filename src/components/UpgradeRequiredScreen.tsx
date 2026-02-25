import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UpgradeRequiredScreenProps {
  minClientVersion: string;
  downloadUrl: string | null;
  onClose?: () => void;
}

export function UpgradeRequiredScreen({
  minClientVersion,
  downloadUrl,
  onClose,
}: UpgradeRequiredScreenProps) {
  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background p-6">
      <div className="max-w-md text-center space-y-6">
        <div className="rounded-full bg-destructive/20 p-4 w-fit mx-auto">
          <svg
            className="h-12 w-12 text-destructive"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-foreground">
          Atualização obrigatória
        </h1>
        <p className="text-muted-foreground">
          Uma nova versão ({minClientVersion}) é necessária para continuar. Feche
          o aplicativo e reinstale a versão mais recente.
        </p>
        {downloadUrl && (
          <Button asChild className="w-full sm:w-auto">
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              Baixar nova versão
            </a>
          </Button>
        )}
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Fechar aplicativo
          </Button>
        )}
      </div>
    </div>
  );
}
