"use client";

import { CONTACT_EMAIL } from "../content";
import { useLang } from "../context/LangContext";
import { Icon } from "./Icons";
import { Reveal, SectionHead } from "./Section";

export default function Contact() {
  const { c } = useLang();
  const href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(c.contact.subject)}`;
  return (
    <section id="contact" className="scroll-mt-28 px-5 pb-40 pt-28 sm:px-8 lg:pt-36">
      <div className="mx-auto max-w-6xl">
        <SectionHead eyebrow={c.contact.eyebrow} title={c.contact.title} sub={c.contact.sub} />
        <Reveal delay={0.15} className="mt-10 flex flex-col items-center gap-5">
          <a href={href} className="btn-primary px-8 py-4 text-base">
            <Icon.mail className="h-5 w-5" /> {c.contact.cta}
          </a>
          <a href={href} className="ink-soft text-sm underline-offset-4 hover:underline">{CONTACT_EMAIL}</a>
          <ul className="mt-2 flex flex-wrap justify-center gap-x-6 gap-y-2">
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
