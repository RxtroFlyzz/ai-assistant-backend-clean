"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLang } from "../context/LangContext";

interface Message {
  role: "user" | "bot";
  key: string;
}

const CONVERSATION: Message[] = [
  { role: "user", key: "how.demo.user1" },
  { role: "bot", key: "how.demo.bot1" },
  { role: "user", key: "how.demo.user2" },
  { role: "bot", key: "how.demo.bot2" },
  { role: "user", key: "how.demo.user3" },
  { role: "bot", key: "how.demo.bot3" },
];

// ms to wait before each message appears (after optional typing)
const DELAYS = [600, 500, 1200, 500, 1000, 500];
// ms the typing indicator shows before a bot message
const TYPING_DURATION = [0, 900, 0, 1100, 0, 950];

export default function ChatDemo() {
  const { t } = useLang();
  const [visible, setVisible] = useState<number[]>([]);
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const loopRef = useRef<{ cancel: () => void } | null>(null);
  const hasStartedRef = useRef(false);

  const runLoop = useCallback(() => {
    let cancelled = false;

    async function loop() {
      while (!cancelled) {
        setVisible([]);
        setTyping(false);
        await sleep(400);

        for (let i = 0; i < CONVERSATION.length; i++) {
          if (cancelled) return;
          await sleep(DELAYS[i]);
          if (cancelled) return;

          // Show typing indicator for bot messages
          if (CONVERSATION[i].role === "bot" && TYPING_DURATION[i] > 0) {
            setTyping(true);
            await sleep(TYPING_DURATION[i]);
            if (cancelled) return;
            setTyping(false);
            await sleep(80);
          }

          setVisible((prev) => [...prev, i]);

          // Auto-scroll the message window to bottom
          requestAnimationFrame(() => {
            scrollRef.current?.scrollTo({ top: 9999, behavior: "smooth" });
          });
        }

        // Pause before looping
        await sleep(3000);
      }
    }

    loop();
    return { cancel: () => { cancelled = true; } };
  }, []);

  // Start animation only when this component enters the viewport
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasStartedRef.current) {
            hasStartedRef.current = true;
            loopRef.current = runLoop();
          }
        });
      },
      { threshold: 0.25 }
    );

    observer.observe(el);
    return () => {
      observer.disconnect();
      loopRef.current?.cancel();
    };
  }, [runLoop]);

  return (
    <div
      ref={containerRef}
      className="glass rounded-2xl overflow-hidden w-full max-w-sm mx-auto shadow-2xl shadow-indigo-900/30"
    >
      {/* ── Header bar ── */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-white/[0.02]">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-md shadow-indigo-500/40">
          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-none">Replai Bot</p>
          <p className="text-xs text-emerald-400 mt-0.5 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
            En ligne
          </p>
        </div>
        <div className="flex gap-1.5 flex-shrink-0">
          {(["bg-red-400/70", "bg-yellow-400/70", "bg-green-400/70"] as const).map((c) => (
            <span key={c} className={`w-2.5 h-2.5 rounded-full ${c}`} />
          ))}
        </div>
      </div>

      {/* ── Message window ── */}
      <div
        ref={scrollRef}
        className="flex flex-col gap-3 p-4 h-72 overflow-y-auto"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        <AnimatePresence initial={false}>
          {CONVERSATION.map((msg, i) =>
            visible.includes(i) ? (
              <motion.div
                key={`msg-${i}`}
                initial={{ opacity: 0, y: 12, scale: 0.94 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.28, ease: "easeOut" }}
                className={`flex items-end gap-2 ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "bot" && (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow shadow-indigo-500/30">
                    <span className="text-white text-[9px] font-bold leading-none">AI</span>
                  </div>
                )}
                <div
                  className={`max-w-[78%] px-3.5 py-2.5 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl rounded-br-sm shadow-md shadow-indigo-500/30"
                      : "glass text-slate-200 rounded-2xl rounded-bl-sm"
                  }`}
                >
                  {t(msg.key)}
                </div>
              </motion.div>
            ) : null
          )}
        </AnimatePresence>

        {/* Typing indicator */}
        <AnimatePresence>
          {typing && (
            <motion.div
              key="typing"
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 4, scale: 0.92 }}
              transition={{ duration: 0.22 }}
              className="flex items-end gap-2"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <span className="text-white text-[9px] font-bold">AI</span>
              </div>
              <div className="glass px-4 py-3 rounded-2xl rounded-bl-sm flex gap-1 items-center">
                <span className="typing-dot w-1.5 h-1.5 rounded-full bg-slate-400" />
                <span className="typing-dot w-1.5 h-1.5 rounded-full bg-slate-400" />
                <span className="typing-dot w-1.5 h-1.5 rounded-full bg-slate-400" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Input bar ── */}
      <div className="px-4 py-3 border-t border-white/10 bg-white/[0.02] flex items-center gap-2">
        <div className="flex-1 glass rounded-full px-4 py-2 text-xs text-slate-500 select-none">
          Écrire un message…
        </div>
        <button
          aria-label="Envoyer"
          className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow shadow-indigo-500/30"
        >
          <svg
            className="w-3.5 h-3.5 text-white rotate-90"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}

function sleep(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms));
}
