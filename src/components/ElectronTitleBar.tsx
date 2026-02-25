import { Minus, Square, X } from "lucide-react";
import { useEffect, useState } from "react";

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

export function ElectronTitleBar() {
  const [isMaximized, setIsMaximized] = useState(false);

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

  return (
    <div
      className="electron-drag flex h-10 shrink-0 items-center justify-between bg-[#0a0a0f] border-b border-white/5 px-2 select-none"
      style={{ WebkitAppRegion: "drag" } as React.CSSProperties}
    >
      <div className="flex items-center gap-3 pl-2">
        <img
          src={import.meta.env.BASE_URL + "App.png"}
          alt="Pulso"
          className="h-7 w-7 object-contain shrink-0"
        />
        <span className="text-sm font-semibold text-white/95 tracking-tight">
          Pulso Tech - Dashboard Operacional Inteligente
        </span>
      </div>

      <div
        className="flex items-stretch"
        style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}
      >
        <button
          type="button"
          onClick={() => api.minimize()}
          className={`${btnBase} text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-500/15 hover:shadow-[0_0_12px_rgba(34,211,238,0.3)]`}
          aria-label="Minimizar"
        >
          <Minus className="h-3.5 w-3.5 stroke-[2.5]" />
        </button>
        <button
          type="button"
          onClick={() => api.maximize()}
          className={`${btnBase} text-cyan-300/80 hover:text-cyan-300 hover:bg-cyan-500/15 hover:shadow-[0_0_12px_rgba(34,211,238,0.3)]`}
          aria-label={isMaximized ? "Restaurar" : "Maximizar"}
        >
          <Square
            className={`h-3 w-3 stroke-[2.5] ${isMaximized ? "fill-cyan-300/30" : ""}`}
          />
        </button>
        <button
          type="button"
          onClick={() => api.close()}
          className={`${btnBase} text-violet-300/80 hover:text-white hover:bg-gradient-to-r hover:from-violet-500/40 hover:to-fuchsia-500/40 hover:shadow-[0_0_14px_rgba(139,92,246,0.4)]`}
          aria-label="Fechar"
        >
          <X className="h-3.5 w-3.5 stroke-[2.5]" />
        </button>
      </div>
    </div>
  );
}
