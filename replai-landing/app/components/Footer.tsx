"use client";

import { useLang } from "../context/LangContext";
import { Logo } from "./Navbar";

export default function Footer() {
  const { c } = useLang();
  return (
    <footer className="border-t border-white/10 px-5 pb-28 pt-10 sm:px-8 sm:pb-44">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 md:flex-row">
        <Logo light />
        <nav className="flex flex-wrap justify-center gap-6">
          {c.nav.links.map((l) => (
            <a key={l.href} href={l.href} className="text-sm text-slate-400 transition-colors hover:text-white">
              {l.label}
            </a>
          ))}
        </nav>
        <p className="text-xs text-slate-500">
          © {new Date().getFullYear()} Replai · aireply.fr · {c.footer.rights}
        </p>
      </div>
    </footer>
  );
}
