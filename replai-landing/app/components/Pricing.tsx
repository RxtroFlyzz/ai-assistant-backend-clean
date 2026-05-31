"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";

export default function Pricing() {
  const { t } = useLang();

  const features = [
    t("price.f1"),
    t("price.f2"),
    t("price.f3"),
    t("price.f4"),
    t("price.f5"),
    t("price.f6"),
    t("price.f7"),
    t("price.f8"),
  ];

  return (
    <section id="pricing" className="relative py-28 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-cta-glow pointer-events-none" />
      <div className="absolute left-1/2 -translate-x-1/2 top-0 w-px h-32 bg-gradient-to-b from-transparent via-indigo-500/40 to-transparent pointer-events-none" />

      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.65 }}
          className="text-center mb-16"
        >
          <span className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 text-xs uppercase tracking-widest text-amber-400 mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            {t("price.badge")}
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl text-white mt-2">
            {t("price.title")}
          </h2>
        </motion.div>

        {/* Pricing card */}
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.96 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="relative rounded-3xl p-px overflow-hidden"
          style={{
            background: "linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #fcd34d 100%)",
          }}
        >
          {/* Inner card */}
          <div
            className="relative rounded-3xl p-8 sm:p-10 overflow-hidden"
            style={{ background: "hsl(260, 87%, 5%)" }}
          >
            {/* Subtle inner glow */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
            <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-80 h-40 bg-indigo-600/15 blur-3xl rounded-full pointer-events-none" />

            {/* Price header */}
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-5 mb-8">
              {/* Left: badge + description */}
              <div className="flex flex-col gap-3">
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-amber-400/10 rounded-full px-3 py-1 border border-amber-400/20 w-fit">
                  ✦ Plan complet
                </span>
                <p className="text-slate-400 text-sm max-w-xs leading-relaxed">
                  Tout inclus, prêt en 24h.<br />
                  Sans engagement, résiliez à tout moment.
                </p>
              </div>

              {/* Right: price display — 499€ is the HERO price */}
              <div className="sm:text-right flex-shrink-0">
                {/* One-time setup — hero price */}
                <div className="flex sm:justify-end items-baseline gap-1.5">
                  <span className="font-display font-bold text-5xl sm:text-6xl text-white leading-none">
                    499€
                  </span>
                </div>
                <div className="text-sm font-medium text-slate-300 mt-1">
                  setup unique (une seule fois)
                </div>

                {/* Monthly — secondary */}
                <div className="mt-3 flex sm:justify-end items-center gap-2">
                  <div className="h-px w-8 bg-white/10" />
                  <span className="text-lg font-semibold text-indigo-300">
                    puis 49€
                    <span className="text-sm font-normal text-slate-400">/mois</span>
                  </span>
                </div>
              </div>
            </div>

            <div className="mb-8" />

            {/* Features grid */}
            <div className="grid sm:grid-cols-2 gap-3 mb-8">
              {features.map((feat, i) => (
                <motion.div
                  key={feat}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-slate-300 text-sm">{feat}</span>
                </motion.div>
              ))}
            </div>

            {/* CTA */}
            <motion.a
              href="#contact"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="group relative w-full flex items-center justify-center gap-2 py-4 rounded-2xl bg-gradient-to-r from-indigo-500 via-purple-500 to-amber-400 text-white font-semibold text-base shadow-xl shadow-indigo-500/30 hover:shadow-indigo-500/50 transition-all duration-200"
            >
              {t("price.cta")}
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </motion.a>
          </div>
        </motion.div>

        {/* Trust signals */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex items-center justify-center gap-6 mt-8 flex-wrap"
        >
          {["🔒 RGPD", "🇫🇷 Hébergement France", "💬 Support FR/EN", "↩️ Sans engagement"].map((item) => (
            <span key={item} className="text-xs text-slate-500">{item}</span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
