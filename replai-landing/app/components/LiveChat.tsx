"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView, useReducedMotion } from "framer-motion";
import { Icon } from "./Icons";
import type { Product } from "../content";

type Msg = { from: "user" | "bot"; text: string; link?: string; time?: string };

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Tant qu'un chat de demo est a l'ecran, on masque les autres bulles
// (accroche du vrai widget, bulle de la mascotte) pour ne pas les superposer.
let demosVisible = 0;
function markDemo(on: boolean) {
  demosVisible = Math.max(0, demosVisible + (on ? 1 : -1));
  document.body.classList.toggle("demo-visible", demosVisible > 0);
}
const spring = { type: "spring", stiffness: 420, damping: 30 } as const;

// Widget de demo qui se joue en boucle : le client tape, l'assistant repond,
// propose le produit, le curseur clique, et la vente s'affiche.
export default function LiveChat({
  brand,
  messages,
  placeholder,
  online,
  product,
  productAt,
  clickAfter,
  sale,
  done,
  dark = false,
  accent = "#111827",
  height = 440,
}: {
  brand: string;
  messages: Msg[];
  placeholder: string;
  online: string;
  product: Product;
  productAt: number;
  clickAfter: number;
  sale: string;
  done?: string;
  dark?: boolean;
  accent?: string;
  height?: number;
}) {
  const reduced = useReducedMotion();
  const root = useRef<HTMLDivElement>(null);
  const btn = useRef<HTMLSpanElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const inView = useInView(root, { amount: 0.35 });
  const near = useInView(root, { amount: 0.05 });

  const [shown, setShown] = useState(0);
  const [typing, setTyping] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [added, setAdded] = useState(false);
  const [toast, setToast] = useState(false);
  const [showDone, setShowDone] = useState(false);
  const [fade, setFade] = useState(false);
  const [cursor, setCursor] = useState({ x: 0, y: 0, on: false, press: false });

  const bg = dark ? "#0f1330" : "#ffffff";
  const bubble = dark ? "rgba(255,255,255,0.07)" : "#f3f4f6";
  const text = dark ? "#e2e8f0" : "#1f2937";
  const border = dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)";

  useEffect(() => {
    if (!near) return;
    markDemo(true);
    return () => markDemo(false);
  }, [near]);

  // Le fil se remplit par le haut et defile tout seul, comme un vrai chat.
  useEffect(() => {
    const el = body.current;
    if (!el) return;
    // On descend en bas, mais jamais au point de cacher le debut du dernier message :
    // une longue reponse (avec fiche produit) reste lisible depuis sa premiere ligne.
    const all = el.querySelectorAll<HTMLElement>("[data-msg]");
    const last = all[all.length - 1];
    const bottom = el.scrollHeight - el.clientHeight;
    const top = last ? Math.min(bottom, last.offsetTop - 16) : bottom;
    el.scrollTo({ top: Math.max(0, top), behavior: shown <= 1 ? "auto" : "smooth" });
  }, [shown, typing, showDone]);

  // Mouvement reduit : on affiche directement l'etat final, sans boucle.
  useEffect(() => {
    if (!reduced) return;
    setShown(messages.length);
    setAdded(true);
    setShowDone(true);
  }, [reduced, messages.length]);

  useEffect(() => {
    if (reduced || !inView) return;
    let alive = true;
    const wait = async (ms: number) => {
      await sleep(ms);
      if (!alive) throw new Error("stop");
    };

    const click = async () => {
      const r = root.current;
      const b = btn.current;
      if (!r || !b) return;
      const rr = r.getBoundingClientRect();
      const br = b.getBoundingClientRect();
      const tx = br.left - rr.left + br.width * 0.6;
      const ty = br.top - rr.top + br.height * 0.5;
      setCursor({ x: rr.width - 40, y: rr.height - 30, on: false, press: false });
      await wait(60);
      setCursor({ x: rr.width - 40, y: rr.height - 30, on: true, press: false });
      await wait(60);
      setCursor({ x: tx, y: ty, on: true, press: false });
      await wait(900);
      setCursor({ x: tx, y: ty, on: true, press: true });
      await wait(170);
      setAdded(true);
      setCursor({ x: tx, y: ty, on: true, press: false });
      await wait(750);
      setCursor((c) => ({ ...c, on: false }));
      await wait(250);
    };

    const run = async () => {
      while (alive) {
        // Le premier message du client est deja la : la fenetre n'est jamais vide.
        setShown(1);
        setTyping(false);
        setDraft("");
        setAdded(false);
        setToast(false);
        setShowDone(false);
        setCursor((c) => ({ ...c, on: false, press: false }));
        setFade(false);
        await wait(500);

        for (let i = 1; i < messages.length; i++) {
          const m = messages[i];
          if (m.from === "user") {
            const t = m.text;
            const step = Math.max(16, Math.min(38, 1300 / t.length));
            for (let k = 1; k <= t.length; k++) {
              setDraft(t.slice(0, k));
              await wait(step);
            }
            await wait(260);
            setSending(true);
            await wait(160);
            setDraft("");
            setSending(false);
            setShown(i + 1);
            await wait(900);
          } else {
            setTyping(true);
            await wait(1700);
            setTyping(false);
            setShown(i + 1);
            // Temps de lecture : environ 16 caracteres par seconde, plus le temps de regarder la fiche produit.
            await wait(Math.max(2200, m.text.length * 60) + (i === productAt ? 1500 : 0));
          }
          if (i === clickAfter) await click();
        }

        if (done) {
          setShowDone(true);
          await wait(450);
        }
        setToast(true);
        await wait(4500);
        setFade(true);
        await wait(550);
      }
    };

    run().catch(() => {});
    return () => {
      alive = false;
    };
  }, [inView, reduced, messages, productAt, clickAfter, done]);

  return (
    <div ref={root} className="relative">
      <AnimatePresence>
        {toast && !fade && (
          <motion.div
            key="toast"
            initial={{ opacity: 0, y: 14, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.9 }}
            transition={spring}
            className="absolute -top-5 left-4 z-20 flex items-center gap-2 rounded-full bg-emerald-500 px-4 py-2 text-[13px] font-semibold text-white shadow-lg shadow-emerald-500/40"
          >
            <Icon.check className="h-4 w-4" /> {sale}
          </motion.div>
        )}
      </AnimatePresence>

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
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />
                <span className="relative h-1.5 w-1.5 rounded-full bg-emerald-400" />
              </span>
              {online}
            </p>
          </div>
        </div>

        <motion.div
          ref={body}
          animate={{ opacity: fade ? 0 : 1 }}
          transition={{ duration: 0.45 }}
          className="livechat-body relative flex flex-col justify-start gap-3 overflow-hidden px-4 py-5"
          style={{ height }}
        >
          <AnimatePresence initial={false}>
            {messages.slice(0, shown).map((m, i) => (
              <motion.div
                key={i}
                data-msg
                layout
                initial={{ opacity: 0, y: 16, scale: 0.94 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={spring}
                className={`flex shrink-0 flex-col ${i === productAt ? "w-[86%]" : "max-w-[86%]"} ${
                  m.from === "user" ? "self-end items-end" : "self-start items-start"
                }`}
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
                  {i === productAt ? (
                    <div
                      className="mt-3 overflow-hidden rounded-xl"
                      style={{ background: dark ? "rgba(255,255,255,0.05)" : "#ffffff", border: `1px solid ${border}` }}
                    >
                      {product.still ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img className="block aspect-[4/3] w-full object-cover" src={`${product.media}.jpg`} alt={product.name} loading="lazy" />
                      ) : (
                        <video
                          className="block aspect-[4/3] w-full object-cover"
                          src={`${product.media}.mp4`}
                          poster={`${product.media}.jpg`}
                          autoPlay
                          muted
                          loop
                          playsInline
                          preload="metadata"
                        />
                      )}
                      <div className="px-3 pb-3 pt-2.5">
                        <div className="flex items-baseline justify-between gap-2 text-[13px] font-semibold">
                          <span>{product.name}</span>
                          <span>{product.price}</span>
                        </div>
                        <p className="text-[11.5px] opacity-60">{product.meta}</p>
                        <motion.span
                          ref={btn}
                          animate={{ backgroundColor: added ? "#10b981" : accent, scale: added ? [1, 1.06, 1] : 1 }}
                          transition={{ duration: 0.35 }}
                          className="mt-2.5 flex items-center justify-center gap-1.5 rounded-lg py-2 text-[12.5px] font-semibold text-white"
                        >
                          {added ? <Icon.check className="h-3.5 w-3.5" /> : <Icon.bag className="h-3.5 w-3.5" />}
                          {added ? product.added : product.add}
                        </motion.span>
                      </div>
                    </div>
                  ) : (
                    m.link && (
                      <span
                        className="mt-2 flex w-fit items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-semibold text-white"
                        style={{ background: accent }}
                      >
                        <Icon.arrow className="h-3 w-3" /> {m.link}
                      </span>
                    )
                  )}
                </div>
                {m.time && (
                  <span className="mt-1 px-1 text-[10.5px] opacity-50" style={{ color: text }}>
                    {m.time}
                  </span>
                )}
              </motion.div>
            ))}

            {typing && (
              <motion.div
                key="typing"
                layout
                initial={{ opacity: 0, y: 10, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={spring}
                className="flex shrink-0 gap-1.5 self-start rounded-2xl px-4 py-3.5"
                style={{ background: bubble, border: `1px solid ${border}`, borderBottomLeftRadius: 6 }}
              >
                {[0, 1, 2].map((d) => (
                  <span key={d} className="typing-dot h-1.5 w-1.5 rounded-full" style={{ background: text }} />
                ))}
              </motion.div>
            )}

            {done && showDone && (
              <motion.div
                key="done"
                layout
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={spring}
                className="mx-auto mt-1 flex shrink-0 items-center gap-2 rounded-full bg-emerald-400/15 px-3 py-1.5 text-[12px] font-semibold text-emerald-500"
                style={dark ? { color: "#6ee7b7" } : undefined}
              >
                <Icon.check className="h-3.5 w-3.5" /> {done}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        <div className="flex items-center gap-2 px-4 pb-4">
          <div
            className="flex-1 truncate rounded-xl px-4 py-2.5 text-[13px]"
            style={{
              background: bubble,
              border: `1px solid ${border}`,
              color: draft ? text : dark ? "rgba(255,255,255,0.35)" : "#9ca3af",
            }}
          >
            {draft ? (
              <>
                {draft}
                <span className="livechat-caret" />
              </>
            ) : (
              placeholder
            )}
          </div>
          <motion.div
            animate={{ scale: sending ? 0.82 : draft ? 1.06 : 1 }}
            transition={{ duration: 0.15 }}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-white"
            style={{ background: accent }}
          >
            <Icon.send className="h-4 w-4" />
          </motion.div>
        </div>
      </div>

      <motion.div
        aria-hidden
        className="pointer-events-none absolute left-0 top-0 z-30"
        initial={false}
        animate={{ x: cursor.x, y: cursor.y, opacity: cursor.on ? 1 : 0, scale: cursor.press ? 0.82 : 1 }}
        transition={{ x: { duration: 0.85, ease: [0.22, 1, 0.36, 1] }, y: { duration: 0.85, ease: [0.22, 1, 0.36, 1] }, opacity: { duration: 0.2 }, scale: { duration: 0.12 } }}
      >
        <svg width="26" height="26" viewBox="0 0 24 24" className="drop-shadow-lg">
          <path d="M5 3l14 7.5-6.2 1.6L10 18.5z" fill="#ffffff" stroke="#0f172a" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
        {cursor.press && <span className="absolute -left-2 -top-2 h-8 w-8 animate-ping rounded-full bg-white/70" />}
      </motion.div>
    </div>
  );
}
