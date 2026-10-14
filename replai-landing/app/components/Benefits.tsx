"use client";

import { useLang } from "../context/LangContext";
import { Icon } from "./Icons";
import { Reveal, SectionHead } from "./Section";

const ICONS = [Icon.clock, Icon.bag, Icon.bolt];

export default function Benefits() {
  const { c } = useLang();
  return (
    <section id="benefices" className="scroll-mt-28 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-6xl">
        <SectionHead eyebrow={c.benefits.eyebrow} title={c.benefits.title} />
        <div className="mt-16 grid gap-5 md:grid-cols-3">
          {c.benefits.items.map((b, i) => {
            const I = ICONS[i];
            return (
              <Reveal key={b.title} delay={i * 0.1}>
                <div className="surface h-full rounded-3xl p-8 shadow-sm">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-600/25">
                    <I className="h-5 w-5" />
                  </div>
                  <h3 className="ink mt-6 font-display text-xl font-semibold">{b.title}</h3>
                  <p className="ink-soft mt-3 leading-relaxed">{b.text}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
