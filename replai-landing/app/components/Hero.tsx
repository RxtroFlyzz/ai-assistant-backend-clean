"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";
import ChatWindow from "./ChatWindow";
import { Icon } from "./Icons";

export default function Hero() {
  const { c } = useLang();
  const ease = [0.22, 1, 0.36, 1] as const;

  return (
    <section className="relative px-5 pb-24 pt-36 sm:px-8 sm:pt-44 lg:pb-32">
      <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16">
        <div>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease }}
            className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/60 px-3.5 py-1.5 text-xs font-semibold text-indigo-700 backdrop-blur"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-600" />
            {c.hero.eyebrow}
          </motion.p>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease }}
            className="mt-6 font-display text-[40px] font-semibold leading-[1.05] tracking-tight text-slate-900 text-balance sm:text-6xl lg:text-[68px]"
          >
            {c.hero.title1}
            <span className="block text-indigo-700">{c.hero.title2}</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25, ease }}
            className="mt-6 max-w-xl text-lg leading-relaxed text-slate-700"
          >
            {c.hero.sub}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4, ease }}
            className="mt-9 flex flex-col gap-3 sm:flex-row"
          >
            <a href="#contact" className="btn-primary px-7 py-3.5 text-base">
              {c.hero.cta} <Icon.arrow className="h-4 w-4" />
            </a>
            <a
              href="#nuit"
              className="inline-flex items-center justify-center rounded-full border border-slate-900/10 bg-white/60 px-7 py-3.5 text-base font-semibold text-slate-800 backdrop-blur transition-colors hover:bg-white/90"
            >
              {c.hero.secondary}
            </a>
          </motion.div>

          <motion.ul
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-8 flex flex-wrap gap-x-6 gap-y-2"
          >
            {c.hero.trust.map((t) => (
              <li key={t} className="flex items-center gap-2 text-sm font-medium text-slate-700">
                <Icon.check className="h-4 w-4 text-indigo-600" /> {t}
              </li>
            ))}
          </motion.ul>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40, rotate: 1.5 }}
          animate={{ opacity: 1, y: 0, rotate: 0 }}
          transition={{ duration: 0.9, delay: 0.3, ease }}
          className="relative mx-auto w-full max-w-[400px]"
        >
          <span className="absolute -top-3 right-5 z-10 rounded-full bg-slate-900 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-white">
            {c.heroChat.label}
          </span>
          <ChatWindow
            brand={c.heroChat.brand}
            messages={c.heroChat.messages}
            placeholder={c.heroChat.placeholder}
            online={c.heroChat.online}
            accent="#1f2937"
          />
        </motion.div>
      </div>
    </section>
  );
}
