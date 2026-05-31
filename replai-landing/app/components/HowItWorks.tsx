"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";
import ChatDemo from "./ChatDemo";

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.65, delay: i * 0.14, ease: "easeOut" as const },
  }),
};

export default function HowItWorks() {
  const { t } = useLang();

  const steps = [
    {
      num: "01",
      title: t("how.step1.title"),
      desc: t("how.step1.desc"),
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      num: "02",
      title: t("how.step2.title"),
      desc: t("how.step2.desc"),
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      ),
    },
    {
      num: "03",
      title: t("how.step3.title"),
      desc: t("how.step3.desc"),
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
  ];

  return (
    <section id="howitworks" className="relative py-28 px-4 overflow-hidden">
      {/* Background accent */}
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.65 }}
          className="text-center mb-20"
        >
          <span className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 text-xs uppercase tracking-widest text-indigo-400 mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            {t("how.badge")}
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl text-white mt-2">
            {t("how.title")}
          </h2>
        </motion.div>

        {/* 2-col layout */}
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: steps */}
          <div className="flex flex-col gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                custom={i}
                variants={fadeUp}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.3 }}
                className="flex gap-5 group"
              >
                {/* Number + connector */}
                <div className="flex flex-col items-center flex-shrink-0">
                  <div className="w-12 h-12 rounded-xl glass flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/20 transition-colors duration-300">
                    {step.icon}
                  </div>
                  {i < steps.length - 1 && (
                    <div className="w-px flex-1 mt-3 bg-gradient-to-b from-indigo-500/40 to-transparent min-h-8" />
                  )}
                </div>

                {/* Content */}
                <div className="pt-2 pb-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs font-mono text-indigo-400/60 font-semibold">{step.num}</span>
                    <h3 className="font-display font-semibold text-lg text-white">{step.title}</h3>
                  </div>
                  <p className="text-slate-400 text-sm leading-relaxed">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Right: animated chat demo */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            {/* Decorative glow behind card */}
            <div className="absolute inset-0 bg-indigo-500/10 blur-3xl rounded-3xl scale-110 pointer-events-none" />
            <div className="relative">
              <ChatDemo />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
