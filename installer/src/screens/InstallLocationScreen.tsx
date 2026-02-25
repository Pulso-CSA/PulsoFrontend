import { useState, useEffect } from "react";
import { FolderOpen } from "lucide-react";

const btnBase = {
  padding: "10px 24px",
  borderRadius: 8,
  fontWeight: 600,
  fontSize: 14,
  cursor: "pointer",
  transition: "all 0.2s",
  border: "none",
};

export default function InstallLocationScreen({
  onNext,
  onBack,
  installPath,
  onInstallPathChange,
}: {
  onNext: () => void;
  onBack: () => void;
  installPath: string;
  onInstallPathChange: (path: string) => void;
}) {
  const [path, setPath] = useState(installPath || "C:\\Program Files\\Pulso");

  useEffect(() => {
    const api = (window as unknown as { pulsoInstaller?: { getDefaultInstallPath?: () => Promise<string> } }).pulsoInstaller;
    if (api?.getDefaultInstallPath) {
      api.getDefaultInstallPath().then((p) => p && setPath((prev) => (prev === "C:\\Program Files\\Pulso" ? p : prev)));
    }
  }, []);

  useEffect(() => {
    onInstallPathChange(path);
  }, [path, onInstallPathChange]);

  const handleBrowse = async () => {
    try {
      const api = (window as unknown as { pulsoInstaller?: { selectInstallDir: () => Promise<string | null> } }).pulsoInstaller;
      if (api?.selectInstallDir) {
        const selected = await api.selectInstallDir();
        if (selected) setPath(selected);
      }
    } catch {
      // Fallback: não faz nada se não estiver no Electron
    }
  };

  return (
    <div
      className="animate-fade-in installer-pulso-bg"
      style={{
        padding: 32,
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, color: "hsl(var(--fg))" }}>
        Onde instalar o Pulso
      </h2>
      <p style={{ fontSize: 14, color: "hsl(var(--muted-fg))", marginBottom: 24 }}>
        Escolha a pasta onde o aplicativo será instalado. Recomendamos manter o padrão.
      </p>
      <div
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          style={{
            flex: 1,
            padding: "12px 16px",
            borderRadius: 8,
            border: "1px solid hsl(var(--border))",
            background: "hsl(var(--muted))",
            color: "hsl(var(--fg))",
            fontSize: 14,
          }}
          placeholder="C:\Program Files\Pulso"
        />
        <button
          onClick={handleBrowse}
          style={{
            ...btnBase,
            background: "hsl(var(--muted))",
            color: "hsl(var(--fg))",
            border: "1px solid hsl(var(--border))",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <FolderOpen size={18} />
          Procurar
        </button>
      </div>
      <div style={{ flex: 1 }} />
      <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
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
        <button onClick={onNext} className="btn-pulso" style={btnBase}>
          Continuar
        </button>
      </div>
    </div>
  );
}
