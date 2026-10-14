"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Icon } from "./Icons";

type Msg = { from: "user" | "bot"; text: string; link?: string; time?: string };

// Reproduction du widget tel que le voient les clients d'une boutique.
export default function ChatWindow({
  brand,
  messages,
  placeholder,
  online,
  dark = false,
  accent = "#111827",
  footer,
}: {
  brand: string;
  messages: Msg[];
  placeholder: string;
  online: string;
  dark?: boolean;
  accent?: string;
  footer?: React.ReactNode;
}) {
  const reduced = useReducedMotion();
  const bg = dark ? "#0f1330" : "#ffffff";
  const bubble = dark ? "rgba(255,255,255,0.07)" : "#f3f4f6";
  const text = dark ? "#e2e8f0" : "#1f2937";
  const border = dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)";

  return (
    <div
      className="w-full overflow-hidden rounded-3xl shadow-2xl"
      style={{ background: bg, border: `1px solid ${border}`, boxShadow: "0 30px 70px -25px rgba(15,23,42,0.45)" }}
    >
      <div className="flex items-center gap-3 px-5 py-4" style={{ background: accent }}>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 font-display text-sm font-bold text-white">
          {brand.charAt(0)}
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Assistant {brand}</p>
          <p className="flex items-center gap-1.5 text-[11px] text-white/80">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> {online}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3 px-4 py-5">
        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={reduced ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.45, delay: 0.25 + i * 0.55 }}
            className={`flex max-w-[86%] flex-col ${m.from === "user" ? "self-end items-end" : "self-start items-start"}`}
          >
            <div
              className="rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed"
              style={
                m.from === "user"
                  ? { background: accent, color: "#fff", borderBottomRightRadius: 6 }
                  : { background: bubble, color: text, border: `1px solid ${border}`, borderBottomLeftRadius: 6 }
              }
            >
              {m.text}
              {m.link && (
                <span
                  className="mt-2 flex w-fit items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-semibold text-white"
                  style={{ background: accent }}
                >
                  <Icon.arrow className="h-3 w-3" /> {m.link}
                </span>
              )}
            </div>
            {m.time && <span className="mt-1 px-1 text-[10.5px] opacity-50" style={{ color: text }}>{m.time}</span>}
          </motion.div>
        ))}
        {footer}
      </div>

      <div className="flex items-center gap-2 px-4 pb-4">
        <div
          className="flex-1 rounded-xl px-4 py-2.5 text-[13px]"
          style={{ background: bubble, border: `1px solid ${border}`, color: dark ? "rgba(255,255,255,0.35)" : "#9ca3af" }}
        >
          {placeholder}
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl text-white" style={{ background: accent }}>
          <Icon.send className="h-4 w-4" />
        </div>
      </div>
    </div>
  );
}
