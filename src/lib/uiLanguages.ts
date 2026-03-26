/** Preferência de idioma da interface (armazenada localmente até haver i18n completo). */
export const PULSO_UI_LANGUAGE_KEY = "pulso_ui_language";

export interface UiLanguageOption {
  code: string;
  label: string;
}

/** Idiomas suportados na UI (rótulos em português). */
export const UI_LANGUAGE_OPTIONS: UiLanguageOption[] = [
  { code: "en", label: "Inglês" },
  { code: "fr", label: "Francês" },
  { code: "pt", label: "Português" },
  { code: "pt-BR", label: "Português (Brasil)" },
  { code: "es", label: "Espanhol" },
  { code: "de", label: "Alemão" },
  { code: "it", label: "Italiano" },
  { code: "rm", label: "Romanche" },
  { code: "sv", label: "Sueco" },
  { code: "nb", label: "Norueguês" },
  { code: "fi", label: "Finlandês" },
  { code: "nl", label: "Holandês" },
  { code: "pl", label: "Polonês" },
  { code: "cs", label: "Tcheco" },
  { code: "hu", label: "Húngaro" },
  { code: "zh", label: "Mandarim (Chinês)" },
  { code: "ms", label: "Malaio" },
  { code: "ta", label: "Tâmil" },
  { code: "ja", label: "Japonês" },
  { code: "ko", label: "Coreano" },
  { code: "hi", label: "Hindi" },
  { code: "id", label: "Indonésio" },
  { code: "fil", label: "Filipino" },
  { code: "th", label: "Tailandês" },
];

export function getStoredUiLanguage(): string {
  if (typeof window === "undefined") return "pt-BR";
  return localStorage.getItem(PULSO_UI_LANGUAGE_KEY) || "pt-BR";
}

export function setStoredUiLanguage(code: string): void {
  localStorage.setItem(PULSO_UI_LANGUAGE_KEY, code);
}

export function uiLanguageLabel(code: string): string {
  return UI_LANGUAGE_OPTIONS.find((o) => o.code === code)?.label ?? code;
}
