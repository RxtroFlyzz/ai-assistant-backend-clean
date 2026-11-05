"use client";

import { ReactNode, RefObject, useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView, useMotionValueEvent, useReducedMotion, useScroll } from "framer-motion";
import { Icon } from "./Icons";
import type { Product } from "../content";

type Msg = { from: "user" | "bot"; text: string; link?: string; time?: string };
export type Chip = { q: string; a: string; add?: boolean };

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const spring = { type: "spring", stiffness: 420, damping: 30 } as const;

// ---------------------------------------------------------------------------
// Outils communs
// ---------------------------------------------------------------------------

// Tant qu'un chat de demo est a l'ecran, on masque les autres bulles
// (accroche du vrai widget, bulle de la mascotte) pour ne pas les superposer.
let demosVisible = 0;
function markDemo(on: boolean) {
  demosVisible = Math.max(0, demosVisible + (on ? 1 : -1));
  document.body.classList.toggle("demo-visible", demosVisible > 0);
}
function useDemoVisible(ref: RefObject<HTMLElement>) {
  const near = useInView(ref, { amount: 0.05 });
  useEffect(() => {
    if (!near) return;
    markDemo(true);
    return () => markDemo(false);
  }, [near]);
}

// Le fil defile tout seul, sans jamais cacher le debut du dernier message.
function useAutoScroll(body: RefObject<HTMLDivElement>, deps: unknown[]) {
  useEffect(() => {
    const el = body.current;
    if (!el) return;
    const all = el.querySelectorAll<HTMLElement>("[data-msg]");
    const last = all[all.length - 1];
    const bottom = el.scrollHeight - el.clientHeight;
    const top = last ? Math.min(bottom, last.offsetTop - 16) : bottom;
    el.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps
}

function palette(dark: boolean) {
  return {
    bg: dark ? "#0f1330" : "#ffffff",
    bubble: dark ? "rgba(255,255,255,0.07)" : "#f3f4f6",
    text: dark ? "#e2e8f0" : "#1f2937",
    border: dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)",
    muted: dark ? "rgba(255,255,255,0.35)" : "#9ca3af",
  };
}

function Toast({ show, text }: { show: boolean; text: string }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="toast"
          initial={{ opacity: 0, y: 14, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.9 }}
          transition={spring}
          className="absolute -top-5 left-4 z-20 flex items-center gap-2 rounded-full bg-emerald-500 px-4 py-2 text-[13px] font-semibold text-white shadow-lg shadow-emerald-500/40"
        >
          <Icon.check className="h-4 w-4" /> {text}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ProductCard({
  product,
  added,
  dark,
  accent,
  onAdd,
}: {
  product: Product;
  added: boolean;
  dark: boolean;
  accent: string;
  onAdd?: () => void;
}) {
  const p = palette(dark);
  return (
    <div className="mt-3 overflow-hidden rounded-xl" style={{ background: dark ? "rgba(255,255,255,0.05)" : "#ffffff", border: `1px solid ${p.border}` }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="block aspect-[16/10] w-full object-cover" src={`${product.media}.jpg`} alt={product.name} loading="lazy" />
      <div className="px-3 pb-3 pt-2.5">
        <div className="flex items-baseline justify-between gap-2 text-[13px] font-semibold">
          <span>{product.name}</span>
          <span>{product.price}</span>
        </div>
        <p className="text-[11.5px] opacity-60">{product.meta}</p>
        <motion.button
          type="button"
          onClick={onAdd}
          disabled={!onAdd || added}
          animate={{ backgroundColor: added ? "#10b981" : accent, scale: added ? [1, 1.06, 1] : 1 }}
          transition={{ duration: 0.35 }}
          className={`mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-[12.5px] font-semibold text-white ${
            onAdd && !added ? "cursor-pointer hover:brightness-110" : "cursor-default"
          }`}
        >
          {added ? <Icon.check className="h-3.5 w-3.5" /> : <Icon.bag className="h-3.5 w-3.5" />}
          {added ? product.added : product.add}
        </motion.button>
      </div>
    </div>
  );
}

function Bubble({
  m,
  dark,
  accent,
  wide,
  children,
}: {
  m: Msg;
  dark: boolean;
  accent: string;
  wide?: boolean;
  children?: ReactNode;
}) {
  const p = palette(dark);
  return (
    <motion.div
      data-msg
      layout
      initial={{ opacity: 0, y: 16, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.94 }}
      transition={spring}
      className={`flex shrink-0 flex-col ${wide ? "w-[86%]" : "max-w-[86%]"} ${
        m.from === "user" ? "self-end items-end" : "self-start items-start"
      }`}
    >
      <div
        className="rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed"
        style={
          m.from === "user"
            ? { background: accent, color: "#fff", borderBottomRightRadius: 6 }
            : { background: p.bubble, color: p.text, border: `1px solid ${p.border}`, borderBottomLeftRadius: 6 }
        }
      >
        {m.text}
        {children}
      </div>
      {m.time && (
        <span className="mt-1 px-1 text-[10.5px] opacity-50" style={{ color: p.text }}>
          {m.time}
        </span>
      )}
    </motion.div>
  );
}

function Typing({ dark }: { dark: boolean }) {
  const p = palette(dark);
  return (
    <motion.div
      key="typing"
      layout
      initial={{ opacity: 0, y: 10, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={spring}
      className="flex shrink-0 gap-1.5 self-start rounded-2xl px-4 py-3.5"
      style={{ background: p.bubble, border: `1px solid ${p.border}`, borderBottomLeftRadius: 6 }}
    >
      {[0, 1, 2].map((d) => (
        <span key={d} className="typing-dot h-1.5 w-1.5 rounded-full" style={{ background: p.text }} />
      ))}
    </motion.div>
  );
}

function Frame({
  brand,
  online,
  accent,
  dark,
  bodyRef,
  bodyClass,
  children,
  footer,
}: {
  brand: string;
  online: string;
  accent: string;
  dark: boolean;
  bodyRef: RefObject<HTMLDivElement>;
  bodyClass: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  const p = palette(dark);
  return (
    <div
      className="w-full overflow-hidden rounded-3xl"
      style={{ background: p.bg, border: `1px solid ${p.border}`, boxShadow: "0 30px 70px -25px rgba(15,23,42,0.45)", color: p.text }}
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
      <div ref={bodyRef} className={`livechat-body relative flex flex-col justify-start gap-3 overflow-hidden px-4 py-5 ${bodyClass}`}>
        {children}
      </div>
      {footer}
    </div>
  );
}

function InputRow({ dark, accent, draft, placeholder, sending }: { dark: boolean; accent: string; draft: string; placeholder: string; sending: boolean }) {
  const p = palette(dark);
  return (
    <div className="flex items-center gap-2 px-4 pb-4">
      <div
        className="flex-1 truncate rounded-xl px-4 py-2.5 text-[13px]"
        style={{ background: p.bubble, border: `1px solid ${p.border}`, color: draft ? p.text : p.muted }}
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
  );
}

// ---------------------------------------------------------------------------
// Hero : le visiteur joue le client en cliquant sur des questions toutes pretes
// ---------------------------------------------------------------------------

export function HeroChat({
  brand,
  intro,
  chips,
  hint,
  replay,
  placeholder,
  online,
  product,
  sale,
  accent = "#1f2937",
}: {
  brand: string;
  intro: Msg[];
  chips: Chip[];
  hint: string;
  replay: string;
  placeholder: string;
  online: string;
  product: Product;
  sale: string;
  accent?: string;
}) {
  const reduced = useReducedMotion();
  const root = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const started = useInView(root, { once: true, amount: 0.3 });
  useDemoVisible(root);

  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [typing, setTyping] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [used, setUsed] = useState<number[]>([]);
  const [added, setAdded] = useState(false);
  const [toast, setToast] = useState(false);
  const [clicked, setClicked] = useState(false);

  const t = useCallback((ms: number) => sleep(reduced ? 0 : ms), [reduced]);

  // Introduction jouee une fois : la question du client, puis la reponse avec le produit.
  useEffect(() => {
    if (!started) return;
    let alive = true;
    (async () => {
      setMsgs([intro[0]]);
      await t(700);
      if (!alive) return;
      setTyping(true);
      await t(1400);
      if (!alive) return;
      setTyping(false);
      setMsgs(intro.slice(0, 2));
      await t(900);
      if (alive) setReady(true);
    })();
    return () => {
      alive = false;
    };
  }, [started]); // eslint-disable-line react-hooks/exhaustive-deps

  // Remet la conversation a jour si on change de langue.
  useEffect(() => {
    if (!ready) return;
    setMsgs(intro.slice(0, 2));
    setUsed([]);
    setAdded(false);
    setToast(false);
  }, [intro]); // eslint-disable-line react-hooks/exhaustive-deps

  useAutoScroll(body, [msgs.length, typing]);

  const ask = async (i: number) => {
    if (busy || !ready || used.includes(i)) return;
    const chip = chips[i];
    setBusy(true);
    setClicked(true);
    setUsed((u) => [...u, i]);
    if (!reduced) {
      for (let k = 1; k <= chip.q.length; k++) {
        setDraft(chip.q.slice(0, k));
        await sleep(22);
      }
      await sleep(180);
      setSending(true);
      await sleep(140);
    }
    setDraft("");
    setSending(false);
    setMsgs((m) => [...m, { from: "user", text: chip.q }]);
    await t(450);
    setTyping(true);
    await t(1300);
    setTyping(false);
    setMsgs((m) => [...m, { from: "bot", text: chip.a }]);
    if (chip.add) {
      await t(300);
      setAdded(true);
      await t(250);
      setToast(true);
    }
    setBusy(false);
  };

  const addIndex = chips.findIndex((c) => c.add);
  const restart = () => {
    if (busy) return;
    setMsgs(intro.slice(0, 2));
    setUsed([]);
    setAdded(false);
    setToast(false);
  };

  const left = chips.map((c, i) => ({ c, i })).filter(({ c, i }) => !used.includes(i) && !(added && c.add));

  return (
    <div ref={root} className="relative">
      <Toast show={toast} text={sale} />
      <Frame
        brand={brand}
        online={online}
        accent={accent}
        dark={false}
        bodyRef={body}
        bodyClass="h-[360px] sm:h-[380px]"
        footer={
          <div>
            <div className="min-h-[52px] px-4 pb-3 pt-2">
              <AnimatePresence>
                {ready && !clicked && (
                  <motion.p
                    key="hint"
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                    className="chip-hint mb-2 flex items-center gap-1.5 text-[11.5px] font-semibold text-indigo-600"
                  >
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-70" />
                      <span className="relative h-2 w-2 rounded-full bg-indigo-500" />
                    </span>
                    {hint}
                  </motion.p>
                )}
              </AnimatePresence>
              <div className="flex flex-wrap gap-2">
                <AnimatePresence initial={false} mode="popLayout">
                  {ready &&
                    left.map(({ c, i }) => (
                      <motion.button
                        key={c.q}
                        type="button"
                        layout
                        initial={{ opacity: 0, scale: 0.85 }}
                        animate={{ opacity: busy ? 0.45 : 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.85 }}
                        transition={spring}
                        onClick={() => ask(i)}
                        disabled={busy}
                        className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-[12.5px] font-semibold text-indigo-700 transition-colors hover:border-indigo-400 hover:bg-indigo-100 disabled:cursor-default"
                      >
                        {c.q}
                      </motion.button>
                    ))}
                  {ready && added && !busy && (
                    <motion.button
                      key="replay"
                      type="button"
                      layout
                      initial={{ opacity: 0, scale: 0.85 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.85 }}
                      transition={spring}
                      onClick={restart}
                      className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[12.5px] font-semibold text-slate-600 hover:bg-slate-50"
                    >
                      <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
                        <path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4" />
                      </svg>
                      {replay}
                    </motion.button>
                  )}
                </AnimatePresence>
              </div>
            </div>
            <InputRow dark={false} accent={accent} draft={draft} placeholder={placeholder} sending={sending} />
          </div>
        }
      >
        <AnimatePresence initial={false}>
          {msgs.map((m, i) => (
            <Bubble key={i + m.text} m={m} dark={false} accent={accent} wide={i === 1}>
              {i === 1 && (
                <ProductCard product={product} added={added} dark={false} accent={accent} onAdd={addIndex >= 0 && ready ? () => ask(addIndex) : undefined} />
              )}
            </Bubble>
          ))}
          {typing && <Typing dark={false} />}
        </AnimatePresence>
      </Frame>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Nuit : la conversation avance au rythme du scroll
// ---------------------------------------------------------------------------

// Seuils de progression (0 = debut de la section epinglee, 1 = fin).
const NIGHT_STEPS = [0.06, 0.24, 0.42, 0.58, 0.72];

export function NightChat({
  target,
  brand,
  messages,
  placeholder,
  online,
  product,
  sale,
  done,
  hint,
  accent = "#4f46e5",
}: {
  target: RefObject<HTMLElement>;
  brand: string;
  messages: Msg[];
  placeholder: string;
  online: string;
  product: Product;
  sale: string;
  done: string;
  hint: string;
  accent?: string;
}) {
  const reduced = useReducedMotion();
  const root = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  useDemoVisible(root);

  const { scrollYProgress } = useScroll({ target, offset: ["start start", "end end"] });
  const [step, setStep] = useState(0);
  useMotionValueEvent(scrollYProgress, "change", (v) => {
    const s = NIGHT_STEPS.filter((x) => v >= x).length;
    setStep((old) => (old === s ? old : s));
  });

  // L'assistant "ecrit" un instant avant que sa reponse apparaisse.
  const [botReady, setBotReady] = useState(false);
  useEffect(() => {
    if (step < 2) {
      setBotReady(false);
      return;
    }
    if (botReady) return;
    const id = setTimeout(() => setBotReady(true), reduced ? 0 : 750);
    return () => clearTimeout(id);
  }, [step, botReady, reduced]);

  const s = reduced ? 5 : step;
  const showBot = s >= 2 && (reduced || botReady);
  const added = s >= 4;

  useAutoScroll(body, [s, showBot]);

  return (
    <div ref={root} className="relative">
      <Toast show={s >= 5} text={sale} />
      <Frame
        brand={brand}
        online={online}
        accent={accent}
        dark
        bodyRef={body}
        bodyClass="h-[270px] sm:h-[400px]"
        footer={<InputRow dark accent={accent} draft="" placeholder={placeholder} sending={false} />}
      >
        <AnimatePresence initial={false}>
          {s === 0 && (
            <motion.div
              key="hint"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="m-auto flex flex-col items-center gap-2 text-center text-[13px] text-white/60"
            >
              <span className="text-[26px] font-semibold text-white/85">02:47</span>
              {hint}
              <svg className="scroll-cue mt-1 h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
                <path d="M6 9l6 6 6-6" />
              </svg>
            </motion.div>
          )}
          {s >= 1 && <Bubble key="u1" m={messages[0]} dark accent={accent} />}
          {s >= 2 && !showBot && <Typing dark />}
          {showBot && (
            <Bubble key="b1" m={messages[1]} dark accent={accent} wide>
              <ProductCard product={product} added={added} dark accent={accent} />
            </Bubble>
          )}
          {s >= 3 && showBot && <Bubble key="u2" m={messages[2]} dark accent={accent} />}
          {added && showBot && (
            <motion.div
              key="done"
              data-msg
              layout
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.85 }}
              transition={spring}
              className="mx-auto mt-1 flex shrink-0 items-center gap-2 rounded-full bg-emerald-400/15 px-3 py-1.5 text-[12px] font-semibold"
              style={{ color: "#6ee7b7" }}
            >
              <Icon.check className="h-3.5 w-3.5" /> {done}
            </motion.div>
          )}
        </AnimatePresence>
      </Frame>
    </div>
  );
}
