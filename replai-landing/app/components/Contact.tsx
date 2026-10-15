"use client";

import { FormEvent, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BACKEND_URL, CONTACT_EMAIL } from "../content";
import { useLang } from "../context/LangContext";
import { Icon } from "./Icons";
import { Reveal, SectionHead } from "./Section";

type Status = "idle" | "sending" | "done" | "error" | "invalid";

const EMAIL_RE = /^[^@\s<>]+@[^@\s<>]+\.[a-zA-Z]{2,}$/;

export default function Contact() {
  const { c, lang } = useLang();
  const f = c.contact.form;
  const [status, setStatus] = useState<Status>("idle");
  const [sentTo, setSentTo] = useState("");

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const get = (k: string) => String(data.get(k) || "").trim();
    const body = {
      shop_url: get("shop"),
      email: get("email"),
      name: get("name"),
      phone: get("phone"),
      website: get("website"),
      lang,
    };
    if (body.shop_url.length < 4 || !EMAIL_RE.test(body.email)) {
      setStatus("invalid");
      return;
    }
    setStatus("sending");
    try {
      const r = await fetch(`${BACKEND_URL}/demo-request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (r.status === 400) { setStatus("invalid"); return; }
      if (!r.ok) throw new Error(String(r.status));
      setSentTo(body.email);
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  const field =
    "w-full rounded-xl border border-white/15 bg-white/[0.06] px-4 py-3 text-[15px] text-white placeholder:text-slate-500 outline-none transition focus:border-indigo-300 focus:bg-white/[0.09] focus:ring-2 focus:ring-indigo-400/30";
  const label = "mb-1.5 block text-sm font-medium text-slate-300";

  return (
    <section id="contact" className="scroll-mt-28 px-5 pb-40 pt-28 sm:px-8 lg:pt-36">
      <div className="mx-auto max-w-6xl">
        <SectionHead eyebrow={c.contact.eyebrow} title={c.contact.title} sub={c.contact.sub} />
        <Reveal delay={0.15} className="mx-auto mt-12 max-w-xl">
          <div className="surface rounded-3xl p-6 sm:p-8">
            <AnimatePresence mode="wait">
              {status === "done" ? (
                <motion.div
                  key="done"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="py-6 text-center"
                  role="status"
                >
                  <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300">
                    <Icon.check className="h-6 w-6" />
                  </span>
                  <p className="ink mt-5 font-display text-2xl font-semibold">{f.successTitle}</p>
                  <p className="ink-soft mt-2">{f.success.replace("{email}", sentTo)}</p>
                  <button
                    type="button"
                    onClick={() => setStatus("idle")}
                    className="accent-ink mt-6 text-sm font-semibold underline-offset-4 hover:underline"
                  >
                    {f.again}
                  </button>
                </motion.div>
              ) : (
                <motion.form key="form" onSubmit={submit} noValidate initial={false} exit={{ opacity: 0 }} className="space-y-4">
                  <div>
                    <label htmlFor="cf-shop" className={label}>{f.shop}</label>
                    <input id="cf-shop" name="shop" required autoComplete="url" placeholder={f.shopPh} className={field} />
                  </div>
                  <div>
                    <label htmlFor="cf-email" className={label}>{f.email}</label>
                    <input id="cf-email" name="email" type="email" required autoComplete="email" placeholder={f.emailPh} className={field} />
                  </div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label htmlFor="cf-name" className={label}>
                        {f.name} <span className="font-normal text-slate-500">({f.optional})</span>
                      </label>
                      <input id="cf-name" name="name" autoComplete="given-name" className={field} />
                    </div>
                    <div>
                      <label htmlFor="cf-phone" className={label}>
                        {f.phone} <span className="font-normal text-slate-500">({f.optional})</span>
                      </label>
                      <input id="cf-phone" name="phone" type="tel" autoComplete="tel" className={field} />
                    </div>
                  </div>
                  {/* Champ piege pour les robots : invisible et ignore par les humains */}
                  <input name="website" tabIndex={-1} autoComplete="off" aria-hidden className="absolute -left-[9999px] h-0 w-0 opacity-0" />

                  {(status === "error" || status === "invalid") && (
                    <p className="rounded-xl bg-rose-500/10 px-4 py-3 text-sm text-rose-200" role="alert">
                      {status === "invalid" ? f.invalid : (
                        <>
                          {f.error}{" "}
                          <a className="underline underline-offset-2" href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(c.contact.subject)}`}>
                            {CONTACT_EMAIL}
                          </a>
                        </>
                      )}
                    </p>
                  )}

                  <button type="submit" disabled={status === "sending"} className="btn-primary w-full px-8 py-4 text-base disabled:opacity-60">
                    {status === "sending" ? f.sending : (<><Icon.send className="h-5 w-5" /> {c.contact.cta}</>)}
                  </button>
                </motion.form>
              )}
            </AnimatePresence>
          </div>
          <ul className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2">
            {c.contact.reassurance.map((r) => (
              <li key={r} className="ink-soft flex items-center gap-2 text-sm">
                <Icon.check className="accent-ink h-4 w-4" /> {r}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}
