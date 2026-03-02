/**
 * LayoutContext — Switch Layout A/B + Tema claro/escuro
 * Persistido em localStorage (backend PATCH /users/me/preferences quando disponível)
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type LayoutMode = "A" | "B";
export type ThemeMode = "light" | "dark";

interface LayoutContextType {
  layoutMode: LayoutMode;
  setLayoutMode: (mode: LayoutMode) => void;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined);

const LAYOUT_KEY = "pulso_layout_mode";
const THEME_KEY = "pulso_theme_mode";

export function LayoutProvider({ children }: { children: ReactNode }) {
  const [layoutMode, setLayoutModeState] = useState<LayoutMode>("A");

  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => {
    if (typeof window !== "undefined") {
      const s = localStorage.getItem(THEME_KEY);
      return s === "light" || s === "dark" ? s : "dark";
    }
    return "dark";
  });

  const setLayoutMode = (mode: LayoutMode) => {
    setLayoutModeState(mode);
    localStorage.setItem(LAYOUT_KEY, mode);
  };

  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);
    localStorage.setItem(THEME_KEY, mode);
  };

  const toggleTheme = () => {
    setThemeModeState((m) => {
      const next = m === "dark" ? "light" : "dark";
      localStorage.setItem(THEME_KEY, next);
      return next;
    });
  };

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("theme-pulso-light", "theme-pulso-medium", "theme-pulso-dark");
    root.classList.add(themeMode === "light" ? "theme-pulso-light" : "theme-pulso-dark");
  }, [themeMode]);

  return (
    <LayoutContext.Provider
      value={{
        layoutMode,
        setLayoutMode,
        themeMode,
        setThemeMode,
        toggleTheme,
      }}
    >
      {children}
    </LayoutContext.Provider>
  );
}

export function useLayoutContext() {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error("useLayoutContext must be used within LayoutProvider");
  return ctx;
}
