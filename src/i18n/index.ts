import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { buildI18nResources, resolveInitialI18nLng, setDocumentHtmlLang } from "@/lib/i18nLanguages";
import { getStoredUiLanguage } from "@/lib/uiLanguages";

const stored = getStoredUiLanguage();

void i18n.use(initReactI18next).init({
  resources: buildI18nResources(),
  lng: resolveInitialI18nLng(stored),
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  defaultNS: "translation",
});

setDocumentHtmlLang(i18n.language);
i18n.on("languageChanged", (lng) => setDocumentHtmlLang(lng));

export default i18n;
