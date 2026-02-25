import { useState, useEffect } from "react";
import { Download, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

declare global {
  interface Window {
    electronAPI?: {
      onUpdateAvailable?: (callback: (info: { version?: string }) => void) => () => void;
      onUpdateDownloaded?: (callback: () => void) => () => void;
      onUpdateProgress?: (callback: (percent: number) => void) => () => void;
      onUpdateError?: (callback: (msg: string) => void) => () => void;
      downloadUpdate?: () => void;
      quitAndInstall?: () => void;
    };
  }
}

type UpdateState = "idle" | "available" | "downloading" | "ready" | "error";

interface UpdateInfo {
  version?: string;
}

export function UpdateAvailableScreen() {
  const [state, setState] = useState<UpdateState>("idle");
  const [info, setInfo] = useState<UpdateInfo>({});
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const api = window.electronAPI;
    if (!api?.onUpdateAvailable) return;

    const unsubAvailable = api.onUpdateAvailable((evt) => {
      setInfo({ version: evt?.version });
      setState("available");
    });
    const unsubDownloaded = api.onUpdateDownloaded?.(() => {
      setState("ready");
    });
    const unsubProgress = api.onUpdateProgress?.((percent) => {
      setProgress(percent);
    });
    const unsubError = api.onUpdateError?.((msg) => {
      setErrorMsg(msg);
      setState("error");
    });

    return () => {
      unsubAvailable?.();
      unsubDownloaded?.();
      unsubProgress?.();
      unsubError?.();
    };
  }, []);

  const handleDownload = () => {
    window.electronAPI?.downloadUpdate?.();
    setState("downloading");
    setProgress(5);
  };

  const handleInstall = () => {
    window.electronAPI?.quitAndInstall?.();
  };

  const handleDismiss = () => {
    setState("idle");
    setErrorMsg(null);
  };

  if (state === "idle") return null;

  return (
    <div className="fixed inset-0 z-[90] flex flex-col items-center justify-center bg-background/95 backdrop-blur-sm p-6">
      <div className="max-w-md w-full space-y-6 rounded-lg border bg-card p-6 shadow-lg">
        {state === "available" && (
          <>
            <h2 className="text-xl font-semibold text-foreground">
              Nova versão disponível
            </h2>
            <p className="text-muted-foreground">
              A versão {info.version ?? "nova"} está disponível. Deseja instalar
              agora?
            </p>
            <div className="flex gap-2">
              <Button onClick={handleDownload} className="flex-1">
                <Download className="mr-2 h-4 w-4" />
                Instalar e reiniciar
              </Button>
              <Button variant="outline" onClick={handleDismiss}>
                Depois
              </Button>
            </div>
          </>
        )}

        {state === "downloading" && (
          <>
            <h2 className="text-xl font-semibold text-foreground">
              Baixando atualização…
            </h2>
            <Progress value={progress} className="h-2" />
            <p className="text-sm text-muted-foreground">{progress}%</p>
          </>
        )}

        {state === "ready" && (
          <>
            <h2 className="text-xl font-semibold text-foreground">
              Atualização pronta
            </h2>
            <p className="text-muted-foreground">
              A atualização foi baixada. Reinicie o aplicativo para aplicar.
            </p>
            <Button onClick={handleInstall} className="w-full">
              <RefreshCw className="mr-2 h-4 w-4" />
              Reiniciar agora
            </Button>
          </>
        )}

        {state === "error" && (
          <>
            <h2 className="text-xl font-semibold text-destructive">
              Erro na atualização
            </h2>
            <p className="text-muted-foreground">{errorMsg ?? "Erro desconhecido"}</p>
            <div className="flex gap-2">
              <Button onClick={handleDownload}>Tentar novamente</Button>
              <Button variant="outline" onClick={handleDismiss}>
                Fechar
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
