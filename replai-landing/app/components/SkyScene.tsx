"use client";

import { ReactNode, useEffect, useMemo, useState } from "react";
import {
  interpolate,
  motion,
  useMotionValueEvent,
  useScroll,
  useTransform,
  useReducedMotion,
  MotionValue,
} from "framer-motion";

// Interpolation calculee en JS (et non par le navigateur) : evite un bug
// des animations de scroll accelerees qui laissait le soleil visible la nuit.
function useMapped<T extends number | string>(progress: MotionValue<number>, input: number[], output: T[]) {
  const map = useMemo(() => interpolate(input, output as any), []); // eslint-disable-line react-hooks/exhaustive-deps
  return useTransform(progress, (v: number) => map(v) as T);
}

// Seuil a partir duquel le texte et les cartes passent en mode nuit.
const NIGHT_AT = 0.46;

// Le ciel suit le scroll : jour -> fin d'apres-midi -> coucher de soleil -> nuit.
const STOPS = [0, 0.22, 0.4, 0.52, 0.64, 1];
const SKY_TOP = ["#4f9fe6", "#62a9e8", "#e9a06c", "#6c4f9e", "#141a45", "#070a1f"];
const SKY_BOTTOM = ["#d7ecff", "#e3f0fb", "#fbd5a1", "#e28d83", "#2b2a68", "#0e1335"];


// Generateur pseudo-aleatoire fixe : memes etoiles cote serveur et navigateur.
function seeded(seed: number) {
  return () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
}

const CLOUDS = [
  { top: "8%", left: "-5%", w: 260, speed: 95, depth: 0.15, delay: 0 },
  { top: "18%", left: "55%", w: 340, speed: 120, depth: 0.25, delay: -40 },
  { top: "34%", left: "15%", w: 200, speed: 80, depth: 0.1, delay: -20 },
  { top: "48%", left: "70%", w: 280, speed: 110, depth: 0.3, delay: -70 },
  { top: "62%", left: "-10%", w: 360, speed: 140, depth: 0.2, delay: -10 },
  { top: "76%", left: "40%", w: 230, speed: 100, depth: 0.12, delay: -55 },
];

function Cloud({ width }: { width: number }) {
  return (
    <svg width={width} viewBox="0 0 220 90" fill="white" aria-hidden>
      <ellipse cx="60" cy="58" rx="52" ry="28" />
      <ellipse cx="105" cy="42" rx="46" ry="36" />
      <ellipse cx="150" cy="56" rx="50" ry="30" />
      <ellipse cx="110" cy="66" rx="80" ry="22" />
    </svg>
  );
}

function CloudLayer({ progress, reduced }: { progress: MotionValue<number>; reduced: boolean }) {
  const opacity = useMapped(progress, [0, 0.4, 0.58, 0.75], [0.95, 0.85, 0.35, 0.08]);
  return (
    <motion.div className="absolute inset-0" style={{ opacity }}>
      {CLOUDS.map((c, i) => (
        <CloudItem key={i} c={c} progress={progress} reduced={reduced} />
      ))}
    </motion.div>
  );
}

function CloudItem({
  c,
  progress,
  reduced,
}: {
  c: (typeof CLOUDS)[number];
  progress: MotionValue<number>;
  reduced: boolean;
}) {
  const y = useMapped(progress, [0, 1], [0, -600 * c.depth]);
  return (
    <motion.div className="absolute" style={{ top: c.top, left: c.left, y }}>
      <div
        className={reduced ? "" : "cloud-drift"}
        style={{ animationDuration: `${c.speed}s`, animationDelay: `${c.delay}s` }}
      >
        <Cloud width={c.w} />
      </div>
    </motion.div>
  );
}

function Stars({ progress }: { progress: MotionValue<number> }) {
  const opacity = useMapped(progress, [0.5, 0.68], [0, 1]);
  const stars = useMemo(() => {
    const r = seeded(42);
    return Array.from({ length: 90 }, () => ({
      x: r() * 100,
      y: r() * 75,
      s: r() < 0.85 ? 1.5 : 2.5,
      d: 2 + r() * 4,
      o: r() * 3,
    }));
  }, []);
  return (
    <motion.div className="absolute inset-0" style={{ opacity }}>
      {stars.map((s, i) => (
        <span
          key={i}
          className="absolute rounded-full bg-white star-twinkle"
          style={{
            left: `${s.x}%`,
            top: `${s.y}%`,
            width: s.s,
            height: s.s,
            animationDuration: `${s.d}s`,
            animationDelay: `${s.o}s`,
          }}
        />
      ))}
    </motion.div>
  );
}

export default function SkyScene({ children }: { children: ReactNode }) {
  const { scrollYProgress } = useScroll();
  const reduced = !!useReducedMotion();

  const top = useMapped(scrollYProgress, STOPS, SKY_TOP);
  const bottom = useMapped(scrollYProgress, STOPS, SKY_BOTTOM);
  const background = useTransform(
    [top, bottom] as MotionValue<string>[],
    ([t, b]: string[]) => `linear-gradient(to bottom, ${t} 0%, ${b} 100%)`
  );

  const sunY = useMapped(scrollYProgress, [0, 0.42], [0, 380]);
  const sunOpacity = useMapped(scrollYProgress, [0, 0.3, 0.42], [1, 1, 0]);
  const sunColor = useMapped(scrollYProgress, [0, 0.25, 0.4], ["#fff6c8", "#ffe08a", "#ff9f5a"]);
  const moonOpacity = useMapped(scrollYProgress, [0.54, 0.68], [0, 1]);
  const moonY = useMapped(scrollYProgress, [0.54, 1], [60, 0]);

  const [night, setNight] = useState(false);
  const check = (v: number) => setNight((n) => (n === v > NIGHT_AT ? n : v > NIGHT_AT));
  useMotionValueEvent(scrollYProgress, "change", check);
  useEffect(() => {
    const id = requestAnimationFrame(() => check(scrollYProgress.get()));
    return () => cancelAnimationFrame(id);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="sky-root relative min-h-screen" data-theme={night ? "night" : "day"}>
      <motion.div aria-hidden className="fixed inset-0 -z-10 overflow-hidden" style={{ background }}>
        <motion.div
          className="absolute right-[12%] top-[10%] h-28 w-28 rounded-full"
          style={{
            y: sunY,
            opacity: sunOpacity,
            backgroundColor: sunColor,
            boxShadow: "0 0 80px 30px rgba(255,214,120,0.45)",
          }}
        />
        <Stars progress={scrollYProgress} />
        <motion.div className="absolute right-[14%] top-[9%]" style={{ opacity: moonOpacity, y: moonY }}>
          <svg width="84" height="84" viewBox="0 0 84 84">
            <defs>
              <mask id="crescent">
                <rect width="84" height="84" fill="white" />
                <circle cx="56" cy="30" r="30" fill="black" />
              </mask>
            </defs>
            <circle cx="42" cy="42" r="34" fill="#f4f1de" mask="url(#crescent)" />
          </svg>
          <div className="absolute inset-0 -z-10 rounded-full blur-2xl" style={{ background: "rgba(244,241,222,0.18)" }} />
        </motion.div>
        <CloudLayer progress={scrollYProgress} reduced={reduced} />
      </motion.div>
      {children}
    </div>
  );
}
