"use client";

import { useRef } from "react";
import { useReducedMotion } from "framer-motion";
import { useLang } from "../context/LangContext";
import { NightChat } from "./LiveChat";
import { SectionHead } from "./Section";

// La section reste epinglee a l'ecran pendant qu'on fait defiler :
// chaque cran de scroll fait avancer la conversation de nuit.
export default function NightShift() {
  const { c } = useLang();
  const reduced = useReducedMotion();
  const ref = useRef<HTMLElement>(null);
  return (
    <section id="nuit" ref={ref} className={`relative scroll-mt-0 ${reduced ? "py-28 lg:py-40" : "h-[260vh]"}`}>
      <div className={reduced ? "px-5 sm:px-8" : "sticky top-0 flex min-h-screen items-center px-5 pb-6 pt-20 sm:px-8 sm:pt-24"}>
        <div className="night-head mx-auto grid w-full max-w-6xl items-center gap-6 sm:gap-8 lg:grid-cols-2 lg:gap-14">
          <SectionHead eyebrow={c.night.eyebrow} title={c.night.title} sub={c.night.sub} center={false} />
          <div className="mx-auto w-full max-w-[400px]">
            <NightChat
              target={ref}
              brand={c.heroChat.brand}
              messages={c.night.chat}
              placeholder={c.heroChat.placeholder}
              online={c.heroChat.online}
              product={c.night.product}
              sale={c.night.sale}
              done={c.night.done}
              hint={c.night.hint}
              accent="#4f46e5"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
