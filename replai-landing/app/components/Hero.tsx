"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";

const VIDEO_URL =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_065045_c44942da-53c6-4804-b734-f9e07fc22e08.mp4";

const CLIENTS = [
  { name: "Plomberie Martin", icon: "🔧" },
  { name: "Coiffure Belle", icon: "✂️" },
  { name: "Restaurant Duo", icon: "🍽️" },
  { name: "Boulangerie Paul", icon: "🥐" },
  { name: "Auto Express", icon: "🚗" },
  { name: "Jardinerie Verte", icon: "🌿" },
];

export default function Hero() {
  const { t } = useLang();
  const videoRef = useRef<HTMLVideoElement>(null);

  /* ── Custom fade loop ── */
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let animFrame: number;
    let phase: "fadein" | "playing" | "fadeout" | "pause" = "fadein";
    let phaseStart = performance.now();
    const FADE_IN = 500;
    const FADE_OUT = 500;
    const PAUSE = 100;

    function tick(now: number) {
      const elapsed = now - phaseStart;
      if (phase === "fadein") {
        video!.style.opacity = String(Math.min(elapsed / FADE_IN, 1));
        if (elapsed >= FADE_IN) { phase = "playing"; phaseStart = now; }
      } else if (phase === "playing") {
        video!.style.opacity = "1";
        /* nothing — driven by timeupdate */
      } else if (phase === "fadeout") {
        video!.style.opacity = String(Math.max(1 - elapsed / FADE_OUT, 0));
        if (elapsed >= FADE_OUT) { phase = "pause"; phaseStart = now; video!.pause(); }
      } else if (phase === "pause") {
        if (elapsed >= PAUSE) {
          video!.currentTime = 0;
          video!.play().catch(() => {});
          phase = "fadein";
          phaseStart = now;
        }
      }
      animFrame = requestAnimationFrame(tick);
    }

    const handleTimeUpdate = () => {
      if (!video) return;
      const remaining = video.duration - video.currentTime;
      if (remaining <= FADE_OUT / 1000 + 0.05 && phase === "playing") {
        phase = "fadeout";
        phaseStart = performance.now();
      }
    };

    video.play().catch(() => {});
    animFrame = requestAnimationFrame(tick);
    video.addEventListener("timeupdate", handleTimeUpdate);

    return () => {
      cancelAnimationFrame(animFrame);
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, []);

  return (
    <section className="relative min-h-screen flex flex-col overflow-hidden">
      {/* ── Background video ── */}
      <video
        ref={videoRef}
        src={VIDEO_URL}
        muted
        playsInline
        preload="auto"
        className="absolute inset-0 w-full h-full object-cover opacity-0 transition-none"
        style={{ opacity: 0 }}
      />

      {/* ── Gradient overlays ── */}
      <div className="video-overlay absolute inset-0 pointer-events-none" />
      <div className="absolute inset-0 bg-hero-glow pointer-events-none" />

      {/* ── Hero content ── */}
      <div className="relative z-10 flex flex-col items-center justify-center flex-1 px-4 pt-32 pb-16 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 text-sm text-slate-300 mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Chatbot IA pour TPEs françaises
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="font-display font-bold text-5xl sm:text-6xl lg:text-7xl xl:text-8xl leading-[1.05] tracking-tight max-w-5xl"
        >
          <span className="text-white">{t("hero.line1")}</span>
          <br />
          <span className="gradient-text">{t("hero.line2")}</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.55 }}
          className="mt-6 text-lg sm:text-xl text-slate-300 max-w-2xl leading-relaxed"
        >
          {t("hero.sub")}
        </motion.p>

        {/* CTA buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.7 }}
          className="mt-10 flex flex-col sm:flex-row items-center gap-4"
        >
          <a
            href="#contact"
            className="group relative inline-flex items-center gap-2 px-8 py-4 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-amber-400 text-white font-semibold text-base shadow-xl shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-105 active:scale-95 transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {t("hero.cta")}
            <span className="absolute inset-0 rounded-full bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
          </a>

          <a
            href="#howitworks"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-full glass text-slate-200 font-medium text-base hover:bg-white/10 hover:text-white transition-all duration-200"
          >
            {t("hero.secondary")}
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </a>
        </motion.div>

        {/* Social proof numbers */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.9 }}
          className="mt-14 flex items-center gap-8 flex-wrap justify-center"
        >
          {[
            { value: "24h", label: "Setup garanti" },
            { value: "24/7", label: "Disponibilité" },
            { value: "+40%", label: "Leads capturés" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="font-display font-bold text-2xl gradient-text">{stat.value}</div>
              <div className="text-xs text-slate-400 mt-0.5">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* ── Logo marquee ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 1.1 }}
        className="relative z-10 w-full pb-8"
      >
        <p className="text-center text-xs text-slate-500 uppercase tracking-widest mb-4">
          {t("hero.trusted")}
        </p>
        <div className="overflow-hidden">
          <div className="flex gap-4 animate-marquee whitespace-nowrap">
            {[...CLIENTS, ...CLIENTS].map((c, i) => (
              <div
                key={i}
                className="inline-flex items-center gap-2 glass rounded-full px-5 py-2.5 text-sm text-slate-300 flex-shrink-0"
              >
                <span className="text-base">{c.icon}</span>
                <span className="font-medium">{c.name}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
