"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { COPY, Copy } from "../content";

export type Lang = "fr" | "en";

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  c: Copy;
}

const LangContext = createContext<LangCtx>({ lang: "fr", setLang: () => {}, c: COPY.fr });

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("fr");

  useEffect(() => {
    if (navigator.language.toLowerCase().startsWith("en")) setLang("en");
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  return (
    <LangContext.Provider value={{ lang, setLang, c: COPY[lang] }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
