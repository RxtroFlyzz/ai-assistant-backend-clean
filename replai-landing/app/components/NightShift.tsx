"use client";

import { useLang } from "../context/LangContext";
import LiveChat from "./LiveChat";
import { Reveal, SectionHead } from "./Section";

export default function NightShift() {
  const { c } = useLang();
  return (
    <section id="nuit" className="scroll-mt-28 px-5 py-28 sm:px-8 lg:py-40">
      <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-2">
        <SectionHead eyebrow={c.night.eyebrow} title={c.night.title} sub={c.night.sub} center={false} />
        <Reveal delay={0.15} className="mx-auto w-full max-w-[400px]">
          <LiveChat
            brand={c.heroChat.brand}
            messages={c.night.chat}
            placeholder={c.heroChat.placeholder}
            online={c.heroChat.online}
            product={c.night.product}
            productAt={1}
            clickAfter={2}
            sale={c.night.sale}
            done={c.night.done}
            accent="#4f46e5"
            dark
          />
        </Reveal>
      </div>
    </section>
  );
}
