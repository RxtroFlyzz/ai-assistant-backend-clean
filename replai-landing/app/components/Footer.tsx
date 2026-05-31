"use client";

import { motion } from "framer-motion";
import { useLang } from "../context/LangContext";

const NAV = [
  { href: "#howitworks", labelFr: "Comment ça marche", labelEn: "How it works" },
  { href: "#features", labelFr: "Fonctionnalités", labelEn: "Features" },
  { href: "#pricing", labelFr: "Tarifs", labelEn: "Pricing" },
  { href: "#contact", labelFr: "Contact", labelEn: "Contact" },
];

export default function Footer() {
  const { lang, t } = useLang();

  return (
    <footer className="relative border-t border-white/5 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex items-center gap-2"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-display font-bold text-xs">R</span>
            </div>
            <span className="font-display font-semibold text-white">
              Re<span className="gradient-text">plai</span>
            </span>
          </motion.div>

          {/* Links */}
          <nav className="flex items-center gap-6 flex-wrap justify-center">
            {NAV.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors duration-200"
              >
                {lang === "fr" ? item.labelFr : item.labelEn}
              </a>
            ))}
          </nav>

          {/* Copyright */}
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} Replai · aireply.fr · {t("footer.rights")}
          </p>
        </div>
      </div>
    </footer>
  );
}
