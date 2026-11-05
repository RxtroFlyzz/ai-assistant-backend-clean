"use client";

import type { CSSProperties } from "react";
import { useLang } from "../context/LangContext";
import { Icon, IconName } from "./Icons";
import { Reveal, SectionHead } from "./Section";

export default function Features() {
  const { c } = useLang();
  return (
    <section id="fonctionnalites" className="scroll-mt-28 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-6xl">
        <SectionHead eyebrow={c.features.eyebrow} title={c.features.title} />
        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {c.features.items.map((f, i) => {
            const I = Icon[f.icon as IconName];
            return (
              <Reveal key={f.title} delay={(i % 3) * 0.08}>
                <div className="surface card-live h-full rounded-3xl p-7" style={{ "--d": `${i * 0.7}s` } as CSSProperties}>
                  <I className="accent-ink icon-bob h-6 w-6" />
                  <h3 className="ink mt-5 font-display text-lg font-semibold">{f.title}</h3>
                  <p className="ink-soft mt-2.5 leading-relaxed">{f.text}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
