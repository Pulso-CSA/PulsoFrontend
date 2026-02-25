import { useState, useEffect } from "react";
import { CheckCircle, AlertCircle } from "lucide-react";

const btnBase = {
  padding: "10px 24px",
  borderRadius: 8,
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
  border: "none",
};

export default function InstallScreen({ onBack, installPath }: { onBack: () => void; installPath?: string }) {
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [installedPath, setInstalledPath] = useState<string | null>(null);
  const [exePath, setExePath] = useState<string | null>(null);

  useEffect(() => {
    const api = (window as unknown as {
      pulsoInstaller?: {
        performInstall?: (p: string) => Promise<{ ok: boolean; error?: string; installPath?: string }>;
        getDefaultInstallPath?: () => Promise<string>;
      };
    }).pulsoInstaller;

    const run = async () => {
      setProgress(10);
      if (!api?.performInstall) {
        setError("Instalação não disponível neste ambiente.");
        setDone(true);
        return;
      }
      let targetPath = (installPath || "").trim();
      if (!targetPath && api.getDefaultInstallPath) {
        targetPath = (await api.getDefaultInstallPath()) || "";
      }
      if (!targetPath) targetPath = "C:\\Program Files\\Pulso";
      setProgress(30);
      try {
        const result = await api.performInstall!(targetPath);
        setProgress(100);
        if (result?.ok) {
          setInstalledPath(result.installPath || null);
          setExePath((result as { exePath?: string }).exePath || null);
          setDone(true);
        } else {
          const r = result as { error?: string; rawError?: string };
          const msg = r.rawError || r.error || "Falha na instalação.";
          setError(msg);
          if (r.rawError) console.error("Instalação falhou (raw):", r.rawError);
          setDone(true);
        }
      } catch (err) {
        const msg = err instanceof Error ? `${err.message}${err.stack ? `\n\n${err.stack}` : ""}` : String(err);
        setError(msg);
        console.error("Instalação falhou (catch):", err);
        setDone(true);
      }
    };

    run();
  }, [installPath]);

  return (
    <div
      className="animate-fade-in installer-pulso-bg"
      style={{
        padding: 32,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
      }}
    >
      {!done ? (
        <>
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: "50%",
              border: "3px solid hsl(var(--muted))",
              borderTopColor: "hsl(var(--primary))",
              animation: "spin 1s linear infinite",
              marginBottom: 24,
            }}
          />
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: "hsl(var(--fg))" }}>
            Instalando...
          </h2>
          <p style={{ fontSize: 14, color: "hsl(var(--muted-fg))", marginBottom: 24 }}>
            Copiando os arquivos do Pulso
          </p>
          <div
            style={{
              width: "100%",
              maxWidth: 320,
              height: 8,
              background: "hsl(var(--muted))",
              borderRadius: 4,
              overflow: "hidden",
              marginBottom: 32,
            }}
          >
            <div
              style={{
                width: `${Math.min(progress, 100)}%`,
                height: "100%",
                background: "hsl(var(--primary))",
                borderRadius: 4,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </>
      ) : error ? (
        <>
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: "50%",
              background: "hsl(0 65% 45% / 0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 24,
            }}
          >
            <AlertCircle size={48} style={{ color: "hsl(0 65% 55%)" }} />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: "hsl(var(--fg))" }}>
            Erro na instalação
          </h2>
          <p style={{ fontSize: 13, color: "hsl(var(--muted-fg))", marginBottom: 24, maxWidth: 500, fontFamily: "monospace", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {error}
          </p>
          <div style={{ display: "flex", gap: 12 }}>
            <button
              onClick={onBack}
              style={{
                ...btnBase,
                background: "hsl(var(--muted))",
                color: "hsl(var(--fg))",
                border: "1px solid hsl(var(--border))",
              }}
            >
              Voltar
            </button>
            <button
              onClick={() => (window as unknown as { pulsoInstaller?: { close?: () => void } }).pulsoInstaller?.close?.()}
              className="btn-pulso"
              style={btnBase}
            >
              Fechar
            </button>
          </div>
        </>
      ) : (
        <>
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: "50%",
              background: "hsl(150 65% 40% / 0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 24,
            }}
          >
            <CheckCircle size={48} style={{ color: "hsl(150 65% 40%)" }} />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: "hsl(var(--fg))" }}>
            Instalação concluída
          </h2>
          <p style={{ fontSize: 14, color: "hsl(var(--muted-fg))", marginBottom: 8 }}>
            O Pulso foi instalado. Um atalho foi criado na área de trabalho.
          </p>
          <p style={{ fontSize: 12, color: "hsl(var(--muted-fg))", marginBottom: 8 }}>
            Pasta de instalação:
          </p>
          <p style={{ fontSize: 12, color: "hsl(var(--primary))", marginBottom: 24, fontFamily: "monospace", wordBreak: "break-all" }}>
            {installedPath || installPath}
          </p>
          <p style={{ fontSize: 13, color: "hsl(var(--muted-fg))", marginBottom: 24 }}>
            Use o atalho na área de trabalho ou execute <strong>Pulso.exe</strong> na pasta de instalação.
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
            {exePath && (
              <button
                onClick={() => {
                  const api = (window as unknown as { pulsoInstaller?: { openPath?: (p: string) => void } }).pulsoInstaller;
                  api?.openPath?.(exePath);
                }}
                style={{
                  ...btnBase,
                  background: "hsl(var(--muted))",
                  color: "hsl(var(--fg))",
                  border: "1px solid hsl(var(--border))",
                }}
              >
                Iniciar Pulso
              </button>
            )}
            <button
              onClick={() => (window as unknown as { pulsoInstaller?: { close?: () => void } }).pulsoInstaller?.close?.()}
              className="btn-pulso"
              style={btnBase}
            >
              Concluir
            </button>
          </div>
        </>
      )}
    </div>
  );
}
