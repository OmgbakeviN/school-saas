import { createContext, useContext, useEffect, useMemo, useState } from "react";
import fr from "./fr";
import en from "./en";

const dictionaries = { fr, en };
const STORAGE_KEY = "be-wise-language";
const I18nContext = createContext(null);

function getValue(object, path) {
  return path.split(".").reduce((value, key) => value?.[key], object);
}

function interpolate(value, variables = {}) {
  if (typeof value !== "string") return value;
  return value.replace(/\{(\w+)\}/g, (_, key) =>
    variables[key] === undefined ? `{${key}}` : String(variables[key])
  );
}

function initialLanguage() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && dictionaries[stored]) return stored;
  return (navigator.language || "fr").toLowerCase().startsWith("en") ? "en" : "fr";
}

export function I18nProvider({ children }) {
  const [language, setLanguageState] = useState(initialLanguage);

  const setLanguage = (next) => {
    if (!dictionaries[next]) return;
    localStorage.setItem(STORAGE_KEY, next);
    setLanguageState(next);
  };

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const value = useMemo(() => ({
    language,
    setLanguage,
    t(path, variables) {
      const raw = getValue(dictionaries[language], path) ?? getValue(fr, path) ?? path;
      return interpolate(raw, variables);
    }
  }), [language]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}
