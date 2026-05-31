"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";

/* ── Clean SVG icon components ─────────────────────────────────────────── */
const IconBrain = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
  </svg>
);

const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <rect width="20" height="16" x="2" y="4" rx="2" />
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
  </svg>
);

const IconBarChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <line x1="18" x2="18" y1="20" y2="10" />
    <line x1="12" x2="12" y1="20" y2="4" />
    <line x1="6" x2="6" y1="20" y2="14" />
    <line x1="2" x2="22" y1="20" y2="20" />
  </svg>
);

const IconGlobe = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
    <path d="M2 12h20" />
  </svg>
);

const IconShield = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const IconZap = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
    <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" />
  </svg>
);

const FEATURES = [
  {
    Icon: IconBrain,
    titleKey: "feat.ai.title",
    descKey: "feat.ai.desc",
    accent: "text-indigo-400",
    bg: "bg-indigo-500/10",
    ring: "group-hover:ring-indigo-500/40",
    glow: "group-hover:shadow-indigo-500/20",
  },
  {
    Icon: IconMail,
    titleKey: "feat.email.title",
    descKey: "feat.email.desc",
    accent: "text-purple-400",
    bg: "bg-purple-500/10",
    ring: "group-hover:ring-purple-500/40",
    glow: "group-hover:shadow-purple-500/20",
  },
  {
    Icon: IconBarChart,
    titleKey: "feat.dashboard.title",
    descKey: "feat.dashboard.desc",
    accent: "text-blue-400",
    bg: "bg-blue-500/10",
    ring: "group-hover:ring-blue-500/40",
    glow: "group-hover:shadow-blue-500/20",
  },
  {
    Icon: IconGlobe,
    titleKey: "feat.multi.title",
    descKey: "feat.multi.desc",
    accent: "text-emerald-400",
    bg: "bg-emerald-500/10",
    ring: "group-hover:ring-emerald-500/40",
    glow: "group-hover:shadow-emerald-500/20",
  },
  {
    Icon: IconShield,
    titleKey: "feat.secure.title",
    descKey: "feat.secure.desc",
    accent: "text-amber-400",
    bg: "bg-amber-500/10",
    ring: "group-hover:ring-amber-500/40",
    glow: "group-hover:shadow-amber-500/20",
  },
  {
    Icon: IconZap,
    titleKey: "feat.fast.title",
    descKey: "feat.fast.desc",
    accent: "text-yellow-400",
    bg: "bg-yellow-500/10",
    ring: "group-hover:ring-yellow-500/40",
    glow: "group-hover:shadow-yellow-500/20",
  },
];

export default function Features() {
  const { t } = useLang();

  return (
    <section id="features" className="relative py-28 px-4 overflow-hidden">
      {/* Bg accents */}
      <div className="absolute right-0 top-0 w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute left-1/4 bottom-0 w-96 h-64 bg-indigo-600/8 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.65 }}
          className="text-center mb-20"
        >
          <span className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 text-xs uppercase tracking-widest text-purple-400 mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
            {t("feat.badge")}
          </span>
          <h2 className="font-display font-bold text-4xl sm:text-5xl text-white mt-2">
            {t("feat.title")}
          </h2>
        </motion.div>

        {/* Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((feat, i) => (
            <motion.div
              key={feat.titleKey}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{
                duration: 0.6,
                delay: i * 0.08,
                ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
              }}
              whileHover={{ y: -4, scale: 1.01 }}
              className={`glow-border glass rounded-2xl p-6 cursor-default group transition-shadow duration-300 hover:shadow-xl ${feat.glow}`}
            >
              {/* Icon container */}
              <div
                className={`w-11 h-11 rounded-xl ${feat.bg} ring-1 ring-white/10 ${feat.ring} flex items-center justify-center mb-5 transition-all duration-300 group-hover:scale-110 group-hover:ring-2`}
              >
                <span className={feat.accent}>
                  <feat.Icon />
                </span>
              </div>

              {/* Text */}
              <h3 className="font-display font-semibold text-white text-lg mb-2 leading-snug">
                {t(feat.titleKey)}
              </h3>
              <p className="text-slate-400 text-sm leading-relaxed">{t(feat.descKey)}</p>

              {/* Animated bottom accent line */}
              <div
                className={`mt-5 h-px w-0 ${feat.bg.replace("/10", "")} opacity-60 group-hover:w-full transition-all duration-500 rounded-full`}
                style={{ background: "currentColor" }}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
