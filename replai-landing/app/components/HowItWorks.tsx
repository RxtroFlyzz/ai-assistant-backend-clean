"use client";

import { useLang } from "../context/LangContext";
import { Reveal, SectionHead } from "./Section";

export default function HowItWorks() {
  const { c } = useLang();
  return (
    <section id="mise-en-route" className="scroll-mt-28 px-5 py-28 sm:px-8 lg:py-36">
      <div className="mx-auto max-w-6xl">
        <SectionHead eyebrow={c.how.eyebrow} title={c.how.title} />
        <ol className="relative mt-16 grid gap-5 md:grid-cols-3">
          {c.how.steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 0.12}>
              <li className="surface h-full list-none rounded-3xl p-8">
                <span className="accent-ink font-display text-sm font-semibold tracking-widest">0{i + 1}</span>
                <h3 className="ink mt-4 font-display text-xl font-semibold">{s.title}</h3>
                <p className="ink-soft mt-3 leading-relaxed">{s.text}</p>
              </li>
            </Reveal>
          ))}
        </ol>
      </div>
    </section>
  );
}
