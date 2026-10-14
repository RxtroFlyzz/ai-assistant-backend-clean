"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useLang } from "../context/LangContext";

export function Logo({ light = false, themed = false }: { light?: boolean; themed?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-indigo-600 shadow-md shadow-indigo-600/30">
        <svg viewBox="0 0 24 24" className="h-4.5 w-4.5" width="18" height="18" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" aria-hidden>
          <path d="M5 6.5h14v9H11l-4 3v-3H5z" />
          <path d="M9.5 11h.01M14.5 11h.01" />
        </svg>
      </span>
      <span className={`font-display text-lg font-semibold tracking-tight ${themed ? "nav-ink" : light ? "text-white" : "text-slate-900"}`}>Replai</span>
    </span>
  );
}

export default function Navbar() {
  const { lang, setLang, c } = useLang();
  const [open, setOpen] = useState(false);

  const LangSwitch = (
    <div className="flex items-center nav-pill rounded-full p-0.5">
      {(["fr", "en"] as const).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          className={`rounded-full px-2.5 py-1 text-xs font-semibold transition-colors ${
            lang === l ? "bg-white text-slate-900 shadow-sm" : "nav-link"
          }`}
          aria-pressed={lang === l}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );

  return (
    <motion.header
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="fixed inset-x-0 top-3 z-50 px-3 sm:top-4 sm:px-6"
    >
      <nav className="mx-auto flex max-w-6xl items-center justify-between nav-shell rounded-full px-4 py-2.5 shadow-lg shadow-slate-900/5 backdrop-blur-xl sm:px-5">
        <a href="#" aria-label="Replai"><Logo themed /></a>

        <div className="hidden items-center gap-7 md:flex">
          {c.nav.links.map((l) => (
            <a key={l.href} href={l.href} className="nav-link text-sm font-medium">
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:block">{LangSwitch}</div>
          <a href="#contact" className="btn-primary hidden px-4 py-2 text-sm md:inline-flex">{c.nav.cta}</a>
          <button className="nav-ink p-2 md:hidden" onClick={() => setOpen((o) => !o)} aria-label="Menu" aria-expanded={open}>
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {open ? <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12" /> : <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="nav-shell mx-auto mt-2 max-w-6xl rounded-3xl p-4 shadow-lg backdrop-blur-xl md:hidden"
          >
            <div className="flex flex-col">
              {c.nav.links.map((l) => (
                <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="nav-link py-2.5 text-sm font-medium">
                  {l.label}
                </a>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-3 border-t pt-3" style={{ borderColor: "var(--nav-border)" }}>
              {LangSwitch}
              <a href="#contact" onClick={() => setOpen(false)} className="btn-primary flex-1 px-4 py-2.5 text-sm">{c.nav.cta}</a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
