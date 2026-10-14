"use client";

import { useLang } from "../context/LangContext";
import { Icon } from "./Icons";
import { Reveal, SectionHead } from "./Section";

export default function Pricing() {
  const { c } = useLang();
  const p = c.pricing;
  return (
    <section id="tarifs" className="scroll-mt-28 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-6xl">
        <SectionHead eyebrow={p.eyebrow} title={p.title} />
        <Reveal delay={0.1} className="mx-auto mt-14 max-w-3xl">
          <div className="relative overflow-hidden rounded-[32px] border border-white/10 bg-[#11163a]/80 p-8 shadow-2xl backdrop-blur-xl sm:p-11">
            <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-indigo-500/25 blur-3xl" />
            <div className="relative grid gap-10 md:grid-cols-[1fr_1.05fr]">
              <div>
                <span className="inline-flex rounded-full bg-amber-300/15 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-amber-200">
                  {p.badge}
                </span>
                <div className="mt-6 flex items-baseline gap-2">
                  <span className="font-display text-6xl font-semibold tracking-tight text-white">{p.price}</span>
                  <span className="text-lg text-slate-400">{p.per}</span>
                </div>
                <dl className="mt-6 space-y-3 text-[15px]">
                  <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-3">
                    <dt className="text-slate-300">{p.setupLabel}</dt>
                    <dd className="flex items-baseline gap-2">
                      <span className="text-slate-500 line-through">{p.setupOld}</span>
                      <span className="font-semibold text-emerald-300">{p.setupNew}</span>
                    </dd>
                  </div>
                  <div className="flex items-center gap-2 font-semibold text-emerald-300">
                    <Icon.check className="h-4 w-4" /> {p.firstMonth}
                  </div>
                  <div className="text-slate-400">{p.noCommit}</div>
                </dl>
                <a href="#contact" className="btn-primary mt-8 w-full px-6 py-3.5 text-base">
                  {p.cta} <Icon.arrow className="h-4 w-4" />
                </a>
                <p className="mt-3 text-center text-xs text-slate-500">{p.note}</p>
              </div>
              <ul className="space-y-3.5 md:border-l md:border-white/10 md:pl-10">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-3 text-[15px] text-slate-200">
                    <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-indigo-500/25 text-indigo-200">
                      <Icon.check className="h-3 w-3" />
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
