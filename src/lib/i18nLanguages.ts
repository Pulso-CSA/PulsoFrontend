import ptBR from "@/locales/pt-BR.json";
import en from "@/locales/en.json";
import { UI_LANGUAGE_OPTIONS } from "@/lib/uiLanguages";

export type PulsoI18nBundle = typeof ptBR;

/** Idiomas com texto completo: pt-BR (português) e en (demais opções do seletor usam bundle EN até haver tradução). */
export function normalizeI18nLanguage(code: string): "pt-BR" | "en" {
  const x = (code || "pt-BR").toLowerCase().replace(/_/g, "-");
  if (x === "pt-br" || x === "pt") return "pt-BR";
  return "en";
}

function bundleFor(code: string): PulsoI18nBundle {
  return normalizeI18nLanguage(code) === "pt-BR" ? ptBR : en;
}

let cachedResources: Record<string, { translation: PulsoI18nBundle }> | null = null;

/** Recursos por código exato do seletor (cada língua listada aponta para pt-BR ou en). */
export function buildI18nResources(): Record<string, { translation: PulsoI18nBundle }> {
  if (cachedResources) return cachedResources;
  const map: Record<string, { translation: PulsoI18nBundle }> = {};
  const add = (code: string) => {
    map[code] = { translation: bundleFor(code) };
  };
  for (const { code } of UI_LANGUAGE_OPTIONS) {
    add(code);
  }
  add("pt-BR");
  add("pt");
  add("en");
  cachedResources = map;
  return map;
}

export function resolveInitialI18nLng(stored: string): string {
  const resources = buildI18nResources();
  if (resources[stored]) return stored;
  return "pt-BR";
}

export function setDocumentHtmlLang(code: string): void {
  if (typeof document === "undefined") return;
  const x = (code || "pt-BR").toLowerCase().replace(/_/g, "-");
  if (x === "pt-br" || x === "pt") {
    document.documentElement.lang = "pt-BR";
    return;
  }
  if (x.startsWith("en")) {
    document.documentElement.lang = "en";
    return;
  }
  document.documentElement.lang = code.split("-")[0] || "en";
}
