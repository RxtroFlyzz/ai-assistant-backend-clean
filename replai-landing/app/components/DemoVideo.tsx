"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";

export default function DemoVideo() {
  const { lang } = useLang();
  const t =
    lang === "en"
      ? { eyebrow: "See it in action", title: "17 seconds to see Replai at work" }
      : { eyebrow: "Replai en action", title: "17 secondes pour voir Replai au travail" };

  return (
    <section id="demo-video" className="relative px-5 pb-24 sm:px-8 lg:pb-32">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="mx-auto max-w-5xl text-center"
      >
        <p className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/60 px-3.5 py-1.5 text-xs font-semibold text-indigo-700 backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-600" />
          {t.eyebrow}
        </p>
        <h2 className="mt-5 font-display text-3xl font-semibold tracking-tight text-slate-900 text-balance sm:text-4xl">
          {t.title}
        </h2>
        <div className="mt-10 overflow-hidden rounded-3xl bg-black shadow-2xl shadow-indigo-900/30 ring-1 ring-slate-900/10">
          <video
            src="/replai-demo.mp4"
            poster="/replai-demo-poster.jpg"
            autoPlay
            muted
            loop
            playsInline
            preload="metadata"
            className="block aspect-video w-full"
          />
        </div>
      </motion.div>
    </section>
  );
}
