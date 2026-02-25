import { useState, useEffect } from "react";
import { Sun, Moon, Minus, Square, X } from "lucide-react";
import WelcomeScreen from "./screens/WelcomeScreen";
import EulaScreen from "./screens/EulaScreen";
import PermissionsScreen from "./screens/PermissionsScreen";
import InstallLocationScreen from "./screens/InstallLocationScreen";
import TutorialScreen from "./screens/TutorialScreen";
import InstallScreen from "./screens/InstallScreen";

type Step = "welcome" | "eula" | "permissions" | "installLocation" | "tutorial" | "install";

declare global {
  interface Window {
    electronAPI?: {
      minimize: () => void;
      maximize: () => void;
      close: () => void;
      isMaximized: () => Promise<boolean>;
    };
  }
}

export default function App() {
  const [step, setStep] = useState<Step>("welcome");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [installPath, setInstallPath] = useState("");
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    const api = window.electronAPI;
    if (!api) return;
    const check = async () => setIsMaximized(await api.isMaximized());
    check();
    const interval = setInterval(check, 500);
    return () => clearInterval(interval);
  }, []);

  const order: Step[] = ["welcome", "eula", "permissions", "installLocation", "tutorial", "install"];

  const nextStep = () => {
    const i = order.indexOf(step);
    if (i < order.length - 1) setStep(order[i + 1]);
  };

  const prevStep = () => {
    const i = order.indexOf(step);
    if (i > 0) setStep(order[i - 1]);
  };

  return (
    <div className={theme === "light" ? "installer-light" : ""} style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Barra de título */}
      <div
        className="installer-header"
        style={{
          height: 44,
          background: "linear-gradient(90deg, hsl(var(--card)), hsl(235 35% 10%))",
          borderBottom: "1px solid hsl(var(--primary) / 0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 16px",
          flexShrink: 0,
          WebkitAppRegion: "drag",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <img src="./App.png" alt="Pulso" style={{ width: 28, height: 28, objectFit: "contain" }} />
          <span style={{ fontSize: 14, fontWeight: 600, color: "hsl(var(--fg))", letterSpacing: "-0.02em" }}>
            Instalador Pulso
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4, WebkitAppRegion: "no-drag" }}>
          {window.electronAPI && (
            <>
              <button
                type="button"
                onClick={() => window.electronAPI?.minimize()}
                style={{
                  width: 44,
                  height: 36,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: "none",
                  background: "transparent",
                  color: "rgba(34, 211, 238, 0.8)",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(34, 211, 238, 0.15)";
                  e.currentTarget.style.color = "rgb(34, 211, 238)";
                  e.currentTarget.style.boxShadow = "0 0 12px rgba(34, 211, 238, 0.3)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "rgba(34, 211, 238, 0.8)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                aria-label="Minimizar"
              >
                <Minus size={14} strokeWidth={2.5} />
              </button>
              <button
                type="button"
                onClick={() => window.electronAPI?.maximize()}
                style={{
                  width: 44,
                  height: 36,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: "none",
                  background: "transparent",
                  color: "rgba(34, 211, 238, 0.8)",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(34, 211, 238, 0.15)";
                  e.currentTarget.style.color = "rgb(34, 211, 238)";
                  e.currentTarget.style.boxShadow = "0 0 12px rgba(34, 211, 238, 0.3)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "rgba(34, 211, 238, 0.8)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                aria-label={isMaximized ? "Restaurar" : "Maximizar"}
              >
                <Square size={12} strokeWidth={2.5} style={{ fill: isMaximized ? "rgba(34, 211, 238, 0.3)" : "none" }} />
              </button>
              <button
                type="button"
                onClick={() => window.electronAPI?.close()}
                style={{
                  width: 44,
                  height: 36,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: "none",
                  background: "transparent",
                  color: "rgba(139, 92, 246, 0.8)",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "linear-gradient(90deg, rgba(139, 92, 246, 0.4), rgba(217, 70, 239, 0.4))";
                  e.currentTarget.style.color = "white";
                  e.currentTarget.style.boxShadow = "0 0 14px rgba(139, 92, 246, 0.4)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "rgba(139, 92, 246, 0.8)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                aria-label="Fechar"
              >
                <X size={14} strokeWidth={2.5} />
              </button>
            </>
          )}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              border: "none",
              background: `hsl(var(--muted))`,
              color: `hsl(var(--fg))`,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s",
            }}
            title={theme === "dark" ? "Modo claro" : "Modo escuro"}
          >
            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>
      </div>

      {/* Conteúdo */}
      <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
        {step === "welcome" && <WelcomeScreen onNext={nextStep} />}
        {step === "eula" && <EulaScreen onNext={nextStep} onBack={prevStep} />}
        {step === "permissions" && <PermissionsScreen onNext={nextStep} onBack={prevStep} />}
        {step === "installLocation" && (
          <InstallLocationScreen
            onNext={nextStep}
            onBack={prevStep}
            installPath={installPath}
            onInstallPathChange={setInstallPath}
          />
        )}
        {step === "tutorial" && <TutorialScreen onNext={nextStep} onBack={prevStep} />}
        {step === "install" && <InstallScreen onBack={prevStep} installPath={installPath} />}
      </div>

      {/* Indicador de progresso */}
      <div
        style={{
          height: 4,
          background: "hsl(var(--muted))",
          display: "flex",
          overflow: "hidden",
        }}
      >
        {order.map((s) => {
          const currentIdx = order.indexOf(step);
          const isActive = step === s;
          const isCompleted = currentIdx > order.indexOf(s);
          return (
            <div
              key={s}
              style={{
                flex: 1,
                background: isActive || isCompleted
                  ? "linear-gradient(90deg, hsl(var(--primary)), hsl(var(--data-ai)))"
                  : "transparent",
                transition: "background 0.3s ease",
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
