"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";

export type Lang = "fr" | "en";

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const LangContext = createContext<LangCtx>({
  lang: "fr",
  setLang: () => {},
  t: (k) => k,
});

export const translations: Record<string, Record<Lang, string>> = {
  // Navbar
  "nav.how": { fr: "Comment ça marche", en: "How it works" },
  "nav.features": { fr: "Fonctionnalités", en: "Features" },
  "nav.pricing": { fr: "Tarifs", en: "Pricing" },
  "nav.contact": { fr: "Contact", en: "Contact" },
  "nav.cta": { fr: "Démarrer maintenant", en: "Get started" },

  // Hero
  "hero.line1": { fr: "Votre client", en: "Your customer" },
  "hero.line2": { fr: "toujours répondu", en: "always answered" },
  "hero.sub": {
    fr: "Un chatbot IA formé sur votre activité, intégré en 24h sur votre site. Répondez à vos clients à toute heure, sans effort.",
    en: "An AI chatbot trained on your business, live on your site in 24h. Answer clients around the clock, effortlessly.",
  },
  "hero.cta": { fr: "Essayer gratuitement", en: "Try for free" },
  "hero.secondary": { fr: "Voir comment ça marche", en: "See how it works" },
  "hero.trusted": { fr: "Déjà adopté par :", en: "Already trusted by:" },

  // How
  "how.badge": { fr: "Simple & Rapide", en: "Simple & Fast" },
  "how.title": { fr: "En marche en 3 étapes", en: "Live in 3 steps" },
  "how.step1.title": { fr: "Configurez l'IA", en: "Configure AI" },
  "how.step1.desc": {
    fr: "Fournissez vos infos : services, horaires, FAQ. L'IA apprend votre métier en quelques minutes.",
    en: "Share your info: services, hours, FAQ. The AI learns your business in minutes.",
  },
  "how.step2.title": { fr: "Intégrez le widget", en: "Integrate the widget" },
  "how.step2.desc": {
    fr: "Une seule ligne de code sur votre site. Compatible WordPress, Wix, Shopify et tout HTML.",
    en: "One line of code on your site. Works with WordPress, Wix, Shopify, and plain HTML.",
  },
  "how.step3.title": {
    fr: "Capturez des clients 24/7",
    en: "Capture clients 24/7",
  },
  "how.step3.desc": {
    fr: "Votre chatbot répond, qualifie et collecte les contacts même la nuit et le week-end.",
    en: "Your chatbot answers, qualifies, and collects contacts even at night and on weekends.",
  },
  "how.demo.user1": {
    fr: "Bonjour, vous êtes ouverts le dimanche ?",
    en: "Hi, are you open on Sundays?",
  },
  "how.demo.bot1": {
    fr: "Bonjour ! Oui, nous sommes ouverts le dimanche de 9h à 13h. Puis-je vous aider avec autre chose ?",
    en: "Hello! Yes, we're open Sundays from 9am to 1pm. Can I help you with anything else?",
  },
  "how.demo.user2": {
    fr: "Quel est le prix d'une coupe homme ?",
    en: "What's the price of a men's haircut?",
  },
  "how.demo.bot2": {
    fr: "Une coupe homme est à partir de 22€. Voulez-vous réserver un créneau ?",
    en: "Men's haircut starts at €22. Would you like to book an appointment?",
  },
  "how.demo.user3": { fr: "Oui s'il vous plaît !", en: "Yes please!" },
  "how.demo.bot3": {
    fr: "Super ! Quel jour vous convient ? Je peux vérifier les disponibilités 🗓️",
    en: "Great! What day works for you? I can check availability 🗓️",
  },

  // Features
  "feat.badge": { fr: "Tout inclus", en: "All included" },
  "feat.title": { fr: "Tout ce qu'il vous faut", en: "Everything you need" },
  "feat.ai.title": { fr: "IA formée sur votre activité", en: "AI trained on your business" },
  "feat.ai.desc": {
    fr: "Connaît vos services, tarifs et horaires. Répond avec précision.",
    en: "Knows your services, prices, and hours. Answers with precision.",
  },
  "feat.email.title": { fr: "Alertes email instantanées", en: "Instant email alerts" },
  "feat.email.desc": {
    fr: "Recevez chaque nouveau contact directement dans votre boîte mail.",
    en: "Receive every new lead directly in your inbox.",
  },
  "feat.dashboard.title": { fr: "Dashboard analytique", en: "Analytics dashboard" },
  "feat.dashboard.desc": {
    fr: "Suivez conversations, leads et performances en temps réel.",
    en: "Track conversations, leads and performance in real time.",
  },
  "feat.multi.title": { fr: "Multilingue automatique", en: "Auto multilingual" },
  "feat.multi.desc": {
    fr: "Détecte et répond dans la langue du visiteur sans configuration.",
    en: "Detects and replies in the visitor's language automatically.",
  },
  "feat.secure.title": { fr: "Données sécurisées (EU)", en: "Secure EU data" },
  "feat.secure.desc": {
    fr: "Hébergement RGPD en Europe. Vos données restent en France.",
    en: "GDPR-compliant hosting in Europe. Your data stays in France.",
  },
  "feat.fast.title": { fr: "Réponse < 1 seconde", en: "< 1 second response" },
  "feat.fast.desc": {
    fr: "Latence ultra-faible pour une expérience fluide et naturelle.",
    en: "Ultra-low latency for a smooth, natural experience.",
  },

  // Pricing
  "price.badge": { fr: "Tarification simple", en: "Simple pricing" },
  "price.title": { fr: "Un seul plan, tout inclus", en: "One plan, all included" },
  "price.setup": { fr: "499€ setup unique", en: "€499 one-time setup" },
  "price.monthly": { fr: "+ 49€/mois", en: "+ €49/month" },
  "price.sub": {
    fr: "Sans engagement. Résiliez à tout moment.",
    en: "No commitment. Cancel anytime.",
  },
  "price.f1": { fr: "IA formée sur votre activité", en: "AI trained on your business" },
  "price.f2": { fr: "Intégration en 24h", en: "24h integration" },
  "price.f3": { fr: "Dashboard analytics", en: "Analytics dashboard" },
  "price.f4": { fr: "Alertes email en temps réel", en: "Real-time email alerts" },
  "price.f5": { fr: "Support prioritaire", en: "Priority support" },
  "price.f6": { fr: "Mises à jour illimitées", en: "Unlimited updates" },
  "price.f7": { fr: "Hébergement RGPD EU", en: "GDPR EU hosting" },
  "price.f8": { fr: "Multilingue inclus", en: "Multilingual included" },
  "price.cta": { fr: "Démarrer mon projet", en: "Start my project" },

  // CTA
  "cta.title": { fr: "Prêt à ne plus manquer aucun client ?", en: "Ready to never miss a client again?" },
  "cta.sub": {
    fr: "Rejoignez des TPE françaises qui répondent 24h/7j grâce à Replai.",
    en: "Join French small businesses answering 24/7 with Replai.",
  },
  "cta.button": { fr: "Nous contacter", en: "Contact us" },

  // Footer
  "footer.rights": { fr: "Tous droits réservés", en: "All rights reserved" },
};

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("fr");

  useEffect(() => {
    const nav = navigator.language.toLowerCase();
    if (nav.startsWith("en")) setLang("en");
    else setLang("fr");
  }, []);

  const t = (key: string): string => {
    const entry = translations[key];
    if (!entry) return key;
    return entry[lang] ?? key;
  };

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
