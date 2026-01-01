import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type ThemeVariant = "neon" | "ocean" | "forest";
export type ThemeMode = "light" | "dark";

interface ThemeContextType {
  themeVariant: ThemeVariant;
  themeMode: ThemeMode;
  setThemeVariant: (variant: ThemeVariant) => void;
  setThemeMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_VARIANT_KEY = "theme-variant";
const THEME_MODE_KEY = "theme-mode";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [themeVariant, setThemeVariantState] = useState<ThemeVariant>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem(THEME_VARIANT_KEY) as ThemeVariant) || "neon";
    }
    return "neon";
  });

  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem(THEME_MODE_KEY) as ThemeMode) || "dark";
    }
    return "dark";
  });

  const setThemeVariant = (variant: ThemeVariant) => {
    setThemeVariantState(variant);
    localStorage.setItem(THEME_VARIANT_KEY, variant);
  };

  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);
    localStorage.setItem(THEME_MODE_KEY, mode);
  };

  const toggleMode = () => {
    setThemeMode(themeMode === "dark" ? "light" : "dark");
  };

  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove all theme classes
    root.classList.remove("light", "dark", "theme-neon", "theme-ocean", "theme-forest");
    
    // Add current theme classes
    root.classList.add(themeMode);
    root.classList.add(`theme-${themeVariant}`);
  }, [themeVariant, themeMode]);

  return (
    <ThemeContext.Provider value={{ themeVariant, themeMode, setThemeVariant, setThemeMode, toggleMode }}>
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
