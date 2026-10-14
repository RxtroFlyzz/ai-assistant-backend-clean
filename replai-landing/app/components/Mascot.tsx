"use client";

import { useState } from "react";
import {
  AnimatePresence,
  Transition,
  motion,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
} from "framer-motion";
import { useLang } from "../context/LangContext";

type Mood = "day" | "work" | "evening" | "night";

function moodFor(p: number): Mood {
  if (p < 0.24) return "day";
  if (p < 0.44) return "work";
  if (p < 0.58) return "evening";
  return "night";
}

const CYAN = "#7ef0ff";

function Robot({ mood, reduced }: { mood: Mood; reduced: boolean }) {
  const sleepy = mood === "evening" || mood === "night";
  const loop = (d: number, extra: Transition = {}): Transition =>
    reduced ? { duration: 0 } : { duration: d, repeat: Infinity, ease: "easeInOut", ...extra };

  return (
    <svg viewBox="0 0 200 220" className="w-full h-auto overflow-visible" aria-hidden>
      <defs>
        <linearGradient id="rb-shell" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#e4e7ff" />
        </linearGradient>
        <linearGradient id="rb-cap" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#6366f1" />
          <stop offset="1" stopColor="#4338ca" />
        </linearGradient>
        <radialGradient id="rb-glow">
          <stop offset="0" stopColor="#a5b4fc" stopOpacity="0.9" />
          <stop offset="1" stopColor="#a5b4fc" stopOpacity="0" />
        </radialGradient>
      </defs>

      <ellipse cx="100" cy="208" rx="52" ry="8" fill="#0f172a" opacity="0.14" />

      {/* Coussin (le soir et la nuit) */}
      <AnimatePresence>
        {mood === "night" && (
          <motion.g
            key="pillow"
            initial={{ opacity: 0, x: -30, rotate: -20 }}
            animate={{ opacity: 1, x: 0, rotate: -12 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ type: "spring", stiffness: 160, damping: 14 }}
            style={{ originX: "52px", originY: "165px" }}
          >
            <rect x="14" y="138" width="78" height="50" rx="22" fill="#f3efff" stroke="#cfc6f7" strokeWidth="2.5" />
            <path d="M26 163 h54" stroke="#d9d2fa" strokeWidth="2" strokeDasharray="3 5" strokeLinecap="round" />
          </motion.g>
        )}
      </AnimatePresence>

      {/* Corps */}
      <rect x="62" y="128" width="76" height="58" rx="26" fill="url(#rb-shell)" stroke="#c9ccf3" strokeWidth="2.5" />
      <circle cx="100" cy="155" r="14" fill="url(#rb-glow)" />
      <circle cx="100" cy="155" r="6" fill="#818cf8" />

      {/* Bras gauche */}
      <rect x="44" y="134" width="22" height="40" rx="11" fill="url(#rb-shell)" stroke="#c9ccf3" strokeWidth="2.5" transform="rotate(14 55 140)" />

      {/* Bras droit : fait coucou le jour */}
      <motion.g
        style={{ originX: "142px", originY: "140px" }}
        animate={mood === "day" ? { rotate: [0, -38, -18, -38, 0] } : { rotate: 0 }}
        transition={mood === "day" ? loop(2.2, { repeatDelay: 2.5 }) : { duration: 0.4 }}
      >
        <rect x="134" y="134" width="22" height="40" rx="11" fill="url(#rb-shell)" stroke="#c9ccf3" strokeWidth="2.5" transform="rotate(-14 145 140)" />
      </motion.g>

      {/* Tete qui flotte doucement */}
      <motion.g animate={reduced ? {} : { y: [0, -3, 0] }} transition={loop(4)}>
        {/* Antenne */}
        <line x1="100" y1="40" x2="100" y2="22" stroke="#c9ccf3" strokeWidth="3" strokeLinecap="round" />
        <motion.circle
          cx="100"
          cy="16"
          r="8"
          fill={mood === "night" ? "#fcd34d" : "#a5b4fc"}
          animate={reduced ? {} : { opacity: [1, 0.55, 1] }}
          transition={loop(2.4)}
        />

        <rect x="38" y="38" width="124" height="94" rx="36" fill="url(#rb-shell)" stroke="#c9ccf3" strokeWidth="2.5" />
        <rect x="54" y="54" width="92" height="62" rx="24" fill="#1e2357" />

        {/* Yeux */}
        {sleepy ? (
          <g stroke={CYAN} strokeWidth="4" strokeLinecap="round" fill="none">
            <path d={mood === "night" ? "M72 84 q8 7 16 0" : "M72 82 h16"} />
            <path d={mood === "night" ? "M112 84 q8 7 16 0" : "M112 82 h16"} />
          </g>
        ) : (
          <motion.g
            style={{ originY: "82px" }}
            animate={reduced ? {} : { scaleY: [1, 1, 0.1, 1] }}
            transition={loop(4.2, { times: [0, 0.9, 0.95, 1], ease: "linear" })}
          >
            <rect x="74" y="72" width="13" height="21" rx="6.5" fill={CYAN} />
            <rect x="113" y="72" width="13" height="21" rx="6.5" fill={CYAN} />
            <circle cx="83" cy="77" r="2.5" fill="white" />
            <circle cx="122" cy="77" r="2.5" fill="white" />
          </motion.g>
        )}

        {/* Bouche */}
        {mood === "evening" ? (
          <motion.ellipse
            cx="100"
            cy="103"
            rx="6"
            ry="3"
            initial={{ ry: 3 }}
            fill={CYAN}
            opacity="0.85"
            animate={reduced ? { ry: 6 } : { ry: [3, 8, 3] }}
            transition={loop(3)}
          />
        ) : (
          <path
            d={mood === "night" ? "M93 103 q7 4 14 0" : "M89 100 q11 10 22 0"}
            stroke={CYAN}
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
          />
        )}

        {/* Joues */}
        <circle cx="62" cy="104" r="7" fill="#ff9fb5" opacity="0.55" />
        <circle cx="138" cy="104" r="7" fill="#ff9fb5" opacity="0.55" />

        {/* Bonnet de nuit */}
        <AnimatePresence>
          {mood === "night" && (
            <motion.g
              key="cap"
              initial={{ y: -60, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -60, opacity: 0 }}
              transition={{ type: "spring", stiffness: 140, damping: 12 }}
            >
              <path d="M44 52 L156 52 L186 2 Z" fill="url(#rb-cap)" />
              <path d="M88 52 L172 26" stroke="#c7d2fe" strokeWidth="5" opacity="0.6" />
              <path d="M126 52 L180 13" stroke="#c7d2fe" strokeWidth="5" opacity="0.6" />
              <rect x="38" y="44" width="124" height="18" rx="9" fill="#f5f3ff" stroke="#ddd6fe" strokeWidth="2" />
              <motion.circle
                cx="186"
                cy="2"
                r="11"
                fill="#f5f3ff"
                stroke="#ddd6fe"
                strokeWidth="2"
                animate={reduced ? {} : { y: [0, 3, 0] }}
                transition={loop(3)}
              />
            </motion.g>
          )}
        </AnimatePresence>
      </motion.g>

      {/* Zzz */}
      {mood === "night" && !reduced && (
        <g fill="#e0e7ff" fontFamily="General Sans, sans-serif" fontWeight="700">
          {[0, 1, 2].map((i) => (
            <motion.text
              key={i}
              x={30 - i * 4}
              y={40}
              fontSize={12 + i * 4}
              initial={{ opacity: 0, y: 0 }}
              animate={{ opacity: [0, 1, 0], y: [-0, -40], x: [30 - i * 4, 14 - i * 8] }}
              transition={{ duration: 3, repeat: Infinity, delay: i * 1, ease: "easeOut" }}
            >
              z
            </motion.text>
          ))}
        </g>
      )}
    </svg>
  );
}

function Bubble({ mood }: { mood: Mood }) {
  const { c } = useLang();
  const text = c.mascot[mood];
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={mood + text}
        initial={{ opacity: 0, y: 8, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -6, scale: 0.96 }}
        transition={{ duration: 0.3 }}
        className="relative rounded-2xl rounded-bl-md px-4 py-2.5 text-[13px] leading-snug shadow-lg backdrop-blur-md whitespace-nowrap"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--surface-border)",
          color: "var(--ink)",
        }}
      >
        <span className="inline-flex items-center gap-2">
          {mood === "night" && (
            <svg className="h-3.5 w-3.5 text-emerald-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
              <path fillRule="evenodd" d="M16.7 5.3a1 1 0 010 1.4l-7.5 7.5a1 1 0 01-1.4 0L3.3 9.7a1 1 0 111.4-1.4l3.8 3.8 6.8-6.8a1 1 0 011.4 0z" clipRule="evenodd" />
            </svg>
          )}
          {text}
          {mood === "work" && (
            <span className="ml-1 inline-flex gap-0.5">
              <span className="typing-dot h-1 w-1 rounded-full bg-current" />
              <span className="typing-dot h-1 w-1 rounded-full bg-current" />
              <span className="typing-dot h-1 w-1 rounded-full bg-current" />
            </span>
          )}
        </span>
      </motion.div>
    </AnimatePresence>
  );
}

export default function Mascot() {
  const { scrollYProgress } = useScroll();
  const reduced = !!useReducedMotion();
  const [mood, setMood] = useState<Mood>("day");

  useMotionValueEvent(scrollYProgress, "change", (v) => {
    const m = moodFor(v);
    if (m !== mood) setMood(m);
  });

  return (
    <div className="pointer-events-none fixed bottom-3 left-4 z-40 flex items-end gap-1 sm:bottom-5 sm:left-6">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, type: "spring", stiffness: 120, damping: 14 }}
        className="w-[62px] sm:w-[124px]"
      >
        <Robot mood={mood} reduced={reduced} />
      </motion.div>
      <div className="mb-16 hidden sm:block">
        <Bubble mood={mood} />
      </div>
    </div>
  );
}
