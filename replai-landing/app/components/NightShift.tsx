"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";
import ChatWindow from "./ChatWindow";
import { Icon } from "./Icons";
import { Reveal, SectionHead } from "./Section";

export default function NightShift() {
  const { c } = useLang();
  return (
    <section id="nuit" className="scroll-mt-28 px-5 py-28 sm:px-8 lg:py-40">
      <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-2">
        <SectionHead eyebrow={c.night.eyebrow} title={c.night.title} sub={c.night.sub} center={false} />
        <Reveal delay={0.15} className="mx-auto w-full max-w-[400px]">
          <ChatWindow
            brand={c.heroChat.brand}
            messages={c.night.chat}
            placeholder={c.heroChat.placeholder}
            online={c.heroChat.online}
            accent="#4f46e5"
            dark
            footer={
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, amount: 0.5 }}
                transition={{ delay: 2, duration: 0.4 }}
                className="mx-auto mt-1 flex items-center gap-2 rounded-full bg-emerald-400/15 px-3 py-1.5 text-[12px] font-semibold text-emerald-300"
              >
                <Icon.check className="h-3.5 w-3.5" /> {c.night.done}
              </motion.div>
            }
          />
        </Reveal>
      </div>
    </section>
  );
}
