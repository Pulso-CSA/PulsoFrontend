import { Minus, Square, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";
import { useLayoutContext } from "@/contexts/LayoutContext";

declare global {
  interface Window {
    electronAPI?: {
      minimize: () => void;
      maximize: () => void;
      close: () => void;
      isMaximized: () => Promise<boolean>;
      openUninstall?: () => Promise<void>;
    };
  }
}

/** Rotas sem barra escura de título: login, recuperação e escolha de perfil */
const MINIMAL_TITLEBAR_PATHS = new Set([
  "/auth",
  "/auth/callback",
  "/forgot-password",
  "/reset-password",
  "/profile-selection",
]);

export function ElectronTitleBar() {
  const { t } = useTranslation();
  const location = useLocation();
  const { themeMode } = useLayoutContext();
  const isLight = themeMode === "light";
  const [isMaximized, setIsMaximized] = useState(false);
  const minimalChrome = MINIMAL_TITLEBAR_PATHS.has(location.pathname);

  useEffect(() => {
    const api = window.electronAPI;
    if (!api) return;
    const check = async () => setIsMaximized(await api.isMaximized());
    check();
    const interval = setInterval(check, 500);
    return () => clearInterval(interval);
  }, []);

  const api = window.electronAPI;
  if (!api) return null;

  const btnBase =
    "w-11 h-9 flex items-center justify-center transition-all duration-200 group";

  const threeButtons = (
    <>
      <button
        type="button"
        onClick={() => api.minimize()}
        className={cn(
          btnBase,
          isLight
            ? "text-muted-foreground hover:text-foreground hover:bg-muted"
            : "text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-500/15 hover:shadow-[0_0_12px_rgba(34,211,238,0.3)]"
        )}
        aria-label={t("electron.minimize")}
      >
        <Minus className="h-3.5 w-3.5 stroke-[2.5]" />
      </button>
      <button
        type="button"
        onClick={() => api.maximize()}
        className={cn(
          btnBase,
          isLight
            ? "text-muted-foreground hover:text-foreground hover:bg-muted"
            : "text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-500/15 hover:shadow-[0_0_12px_rgba(34,211,238,0.3)]"
        )}
        aria-label={isMaximized ? t("electron.restore") : t("electron.maximize")}
      >
        <Square
          className={cn(
            "h-3 w-3 stroke-[2.5]",
            isMaximized && (isLight ? "fill-foreground/25" : "fill-cyan-300/30")
          )}
        />
      </button>
      <button
        type="button"
        onClick={() => api.close()}
        className={cn(
          btnBase,
          isLight
            ? "text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            : "text-violet-300/80 hover:text-white hover:bg-gradient-to-r hover:from-violet-500/40 hover:to-fuchsia-500/40 hover:shadow-[0_0_14px_rgba(139,92,246,0.4)]"
        )}
        aria-label={t("electron.close")}
      >
        <X className="h-3.5 w-3.5 stroke-[2.5]" />
      </button>
    </>
  );

  /* Login / recuperação: sem faixa escura — arrastar pelo topo; botões flutuantes com vidro */
  if (minimalChrome) {
    return (
      <>
        <div
          className="electron-drag fixed top-0 left-0 right-0 z-[90] h-10 select-none bg-transparent"
          style={{ WebkitAppRegion: "drag" } as React.CSSProperties}
          aria-hidden
        />
        <div
          className={cn(
            "fixed top-2 right-2 z-[100] flex items-stretch rounded-lg overflow-hidden backdrop-blur-md shadow-lg pointer-events-auto",
            isLight
              ? "border border-border bg-background/85"
              : "border border-white/10 bg-background/40"
          )}
          style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}
        >
          {threeButtons}
        </div>
      </>
    );
  }

  return (
    <>
      <div
        className={cn(
          "electron-drag fixed top-0 left-0 right-0 z-[100] flex h-10 shrink-0 items-center justify-between px-2 select-none border-b",
          isLight ? "bg-background border-border" : "bg-[#0a0a0f] border-white/5"
        )}
        style={{ WebkitAppRegion: "drag" } as React.CSSProperties}
      >
        <div className="flex items-center gap-2 pl-2">
          <img
            src={import.meta.env.BASE_URL + "App.png"}
            alt="Pulso"
            className="h-5 w-5 object-contain shrink-0"
          />
          <span
            className={cn(
              "text-sm font-semibold tracking-tight",
              isLight ? "text-foreground" : "text-white/95"
            )}
          >
            Pulso Tech
          </span>
        </div>
        <div
          className="flex items-stretch"
          style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}
        >
          {threeButtons}
        </div>
      </div>
      <div className="h-10 shrink-0" aria-hidden />
    </>
  );
}
