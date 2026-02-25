import { createContext, useContext, useEffect, useState, ReactNode } from "react";

/** Temas PULSO oficiais: Claro, Médio, Escuro */
export type ThemePulso = "light" | "medium" | "dark";

/** @deprecated Use themePulso. Mantido para compatibilidade. */
export type ThemeVariant = "neon" | "classic" | "emerald" | "slate" | "fuchsia";
export type ThemeMode = "light" | "dark";

interface ThemeContextType {
  /** Tema PULSO atual (Claro / Médio / Escuro) */
  themePulso: ThemePulso;
  setThemePulso: (theme: ThemePulso) => void;
  /** @deprecated Use themePulso */
  themeVariant: ThemeVariant;
  themeMode: ThemeMode;
  setThemeVariant: (variant: ThemeVariant) => void;
  setThemeMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_PULSO_KEY = "theme-pulso";
const THEME_VARIANT_KEY = "theme-variant";
const THEME_MODE_KEY = "theme-mode";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [themePulso, setThemePulsoState] = useState<ThemePulso>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(THEME_PULSO_KEY);
      if (stored === "light" || stored === "medium" || stored === "dark") return stored;
      return "medium";
    }
    return "medium";
  });

  const [themeVariant, setThemeVariantState] = useState<ThemeVariant>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(THEME_VARIANT_KEY);
      const valid: ThemeVariant[] = ["neon", "classic", "emerald", "slate", "fuchsia"];
      if (stored && valid.includes(stored as ThemeVariant)) return stored as ThemeVariant;
      return "neon";
    }
    return "neon";
  });

  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem(THEME_MODE_KEY) as ThemeMode) || "dark";
    }
    return "dark";
  });

  const setThemePulso = (theme: ThemePulso) => {
    setThemePulsoState(theme);
    localStorage.setItem(THEME_PULSO_KEY, theme);
  };

  const setThemeVariant = (variant: ThemeVariant) => {
    setThemeVariantState(variant);
    localStorage.setItem(THEME_VARIANT_KEY, variant);
  };

  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);
    localStorage.setItem(THEME_MODE_KEY, mode);
  };

  const toggleMode = () => {
    setThemeModeState((m) => (m === "dark" ? "light" : "dark"));
  };

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove(
      "light", "dark",
      "theme-neon", "theme-ocean", "theme-forest", "theme-classic",
      "theme-terracotta", "theme-emerald", "theme-slate", "theme-rose", "theme-fuchsia",
      "theme-pulso-light", "theme-pulso-medium", "theme-pulso-dark"
    );
    root.classList.add(`theme-pulso-${themePulso}`);
  }, [themePulso]);

  return (
    <ThemeContext.Provider value={{
      themePulso,
      setThemePulso,
      themeVariant,
      themeMode,
      setThemeVariant,
      setThemeMode,
      toggleMode,
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useThemeContext must be used within a ThemeProvider");
  }
  return context;
}
