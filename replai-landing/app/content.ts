// Tous les textes du site, en francais et en anglais.

export const CONTACT_EMAIL = "contact@aireply.fr";

type Msg = { from: "user" | "bot"; text: string; link?: string; time?: string };

const fr = {
  nav: {
    links: [
      { href: "#benefices", label: "Ce que ça change" },
      { href: "#fonctionnalites", label: "Fonctionnalités" },
      { href: "#tarifs", label: "Tarifs" },
      { href: "#contact", label: "Contact" },
    ],
    cta: "Demander ma démo",
  },
  hero: {
    eyebrow: "Assistant IA pour boutiques en ligne",
    title1: "Vos clients ont des questions.",
    title2: "Même à 3 h du matin.",
    sub: "Replai leur répond à votre place, à toute heure : tailles, stocks, livraison, retours. Moins de ventes perdues, moins de messages à traiter.",
    cta: "Demander ma démo",
    secondary: "Voir un exemple",
    trust: ["Compatible Shopify", "Répond dans la langue du client", "Sans engagement"],
  },
  heroChat: {
    brand: "Maison Nuage",
    label: "Exemple",
    messages: [
      { from: "user", text: "Bonjour, le hoodie gris taille comment ? Je fais 1m80." },
      { from: "bot", text: "Il taille un peu grand : à 1m80, le M vous ira parfaitement. Il est en stock dans cette taille.", link: "Voir : Hoodie Nuage gris" },
      { from: "user", text: "Et je le reçois quand ?" },
      { from: "bot", text: "Commandé aujourd'hui, il part demain : livraison en 2 à 3 jours, offerte dès 50 €." },
    ] as Msg[],
    placeholder: "Écrivez votre message…",
    online: "En ligne",
  },
  benefits: {
    eyebrow: "Ce que ça change",
    title: "Chaque question sans réponse est une vente qui s'éloigne.",
    items: [
      { title: "Une réponse immédiate", text: "Vos clients ont leur réponse en quelques secondes, le soir, le week-end et pendant vos drops, au moment où ils hésitent." },
      { title: "Plus de ventes", text: "Un client rassuré sur sa taille ou son délai de livraison va au bout de sa commande au lieu de fermer l'onglet." },
      { title: "Du temps retrouvé", text: "Les questions répétitives sont traitées pour vous. Vous gardez votre énergie pour votre marque et vos vrais échanges clients." },
    ],
  },
  how: {
    eyebrow: "Mise en route",
    title: "Opérationnel en 24 heures.",
    steps: [
      { title: "On prépare votre assistant", text: "À partir de votre boutique : vos produits, votre ton, vos conditions. Vous n'avez rien à rédiger." },
      { title: "Vous validez la démo", text: "Vous le testez comme un client avant qu'il soit en ligne, et on l'ajuste avec vous." },
      { title: "Il est en ligne", text: "Il répond à vos clients et vous transmet ceux qui veulent échanger avec vous." },
    ],
  },
  features: {
    eyebrow: "Fonctionnalités",
    title: "Pensé pour les marques qui vendent en ligne.",
    items: [
      { icon: "catalog", title: "Toujours à jour", text: "Il connaît vos produits, vos prix et vos stocks par taille. Un nouveau drop ? Il le connaît aussi." },
      { icon: "size", title: "Conseil taille", text: "Il aide vos clients à choisir la bonne taille et propose une alternative quand elle est épuisée." },
      { icon: "link", title: "Droit au produit", text: "Chaque réponse renvoie vers la bonne fiche produit, pour passer de la question à l'achat en un clic." },
      { icon: "lead", title: "Clients à rappeler", text: "Quand un client veut vous parler, vous recevez ses coordonnées par email, immédiatement." },
      { icon: "dashboard", title: "Tableau de bord", text: "Toutes les conversations au même endroit, pour savoir ce que vos clients demandent vraiment." },
      { icon: "brand", title: "À vos couleurs", text: "Son apparence et son ton s'accordent à votre marque. Il parle la langue de chaque client." },
    ],
  },
  night: {
    eyebrow: "Pendant que vous dormez",
    title: "Vous vous reposez. Lui, il répond.",
    sub: "Une bonne partie des achats en ligne se fait le soir. Votre assistant reste là pour rassurer, conseiller et accompagner jusqu'à la commande.",
    chat: [
      { from: "user", text: "Vous livrez en Belgique ? J'aimerais commander ce soir.", time: "02:47" },
      { from: "bot", text: "Oui, nous livrons en Belgique en 3 à 5 jours ouvrés. Vous pouvez commander dès maintenant.", time: "02:47", link: "Voir mon panier" },
      { from: "user", text: "Parfait, je finalise.", time: "02:48" },
    ] as Msg[],
    done: "Commande passée à 02:49",
  },
  pricing: {
    eyebrow: "Tarifs",
    title: "Un seul plan. Tout est inclus.",
    badge: "Offre de lancement",
    price: "49 €",
    per: "/ mois",
    setupLabel: "Frais de mise en place",
    setupOld: "499 €",
    setupNew: "199 €",
    noCommit: "Sans engagement, résiliable à tout moment",
    note: "Offre réservée à nos premières marques partenaires.",
    features: [
      "Assistant connecté à votre catalogue",
      "Conseil tailles, livraison et retours",
      "Clients à rappeler transmis par email",
      "Tableau de bord des conversations",
      "Aux couleurs de votre marque",
      "Réponses dans la langue du client",
      "Ajustements inclus",
    ],
    cta: "Demander ma démo",
  },
  contact: {
    eyebrow: "Contact",
    title: "Découvrez votre assistant avant de décider.",
    sub: "Envoyez-nous l'adresse de votre boutique : nous vous préparons une démo personnalisée sous 24 heures. Si vous voulez en parler, on organise un appel.",
    cta: "Demander ma démo",
    subject: "Démo Replai pour ma boutique",
    reassurance: ["Démo gratuite", "Réponse sous 24 h", "Sans engagement"],
  },
  mascot: {
    day: "Bonjour ! Une question sur une taille ?",
    work: "Je réponds à vos clients…",
    evening: "Il se fait tard… je reste là.",
    night: "Réponse envoyée à 02:47",
  },
  footer: { rights: "Tous droits réservés" },
};

export type Copy = typeof fr;

const en: Copy = {
  nav: {
    links: [
      { href: "#benefices", label: "Why it matters" },
      { href: "#fonctionnalites", label: "Features" },
      { href: "#tarifs", label: "Pricing" },
      { href: "#contact", label: "Contact" },
    ],
    cta: "Get my demo",
  },
  hero: {
    eyebrow: "AI assistant for online stores",
    title1: "Your customers have questions.",
    title2: "Even at 3 a.m.",
    sub: "Replai answers them for you, around the clock: sizes, stock, shipping, returns. Fewer lost sales, fewer messages to handle.",
    cta: "Get my demo",
    secondary: "See an example",
    trust: ["Works with Shopify", "Replies in the customer's language", "No commitment"],
  },
  heroChat: {
    brand: "Maison Nuage",
    label: "Example",
    messages: [
      { from: "user", text: "Hi, how does the grey hoodie fit? I'm 1.80 m." },
      { from: "bot", text: "It runs slightly large: at 1.80 m, a M will fit you perfectly. It's in stock in that size.", link: "View: Grey Nuage hoodie" },
      { from: "user", text: "When would I get it?" },
      { from: "bot", text: "Order today and it ships tomorrow: delivery in 2 to 3 days, free over €50." },
    ],
    placeholder: "Type your message…",
    online: "Online",
  },
  benefits: {
    eyebrow: "Why it matters",
    title: "Every unanswered question is a sale slipping away.",
    items: [
      { title: "Instant answers", text: "Customers get their answer in seconds, in the evening, at weekends and during your drops, right when they hesitate." },
      { title: "More sales", text: "A customer who is reassured about size or delivery time completes the order instead of closing the tab." },
      { title: "Time back", text: "Repetitive questions are handled for you. Keep your energy for your brand and the conversations that matter." },
    ],
  },
  how: {
    eyebrow: "Getting started",
    title: "Up and running in 24 hours.",
    steps: [
      { title: "We set up your assistant", text: "Based on your store: your products, your tone, your policies. Nothing for you to write." },
      { title: "You approve the demo", text: "Test it like a customer before it goes live, and we fine-tune it with you." },
      { title: "It goes live", text: "It answers your customers and passes on those who want to talk to you." },
    ],
  },
  features: {
    eyebrow: "Features",
    title: "Built for brands that sell online.",
    items: [
      { icon: "catalog", title: "Always up to date", text: "It knows your products, prices and stock by size. New drop? It knows that too." },
      { icon: "size", title: "Size advice", text: "It helps customers pick the right size and suggests an alternative when one is sold out." },
      { icon: "link", title: "Straight to the product", text: "Every answer links to the right product page, from question to purchase in one click." },
      { icon: "lead", title: "Callback requests", text: "When a customer wants to talk to you, you get their details by email, instantly." },
      { icon: "dashboard", title: "Dashboard", text: "Every conversation in one place, so you know what your customers really ask." },
      { icon: "brand", title: "On brand", text: "Its look and tone match your brand. It speaks each customer's language." },
    ],
  },
  night: {
    eyebrow: "While you sleep",
    title: "You rest. It keeps answering.",
    sub: "A large share of online shopping happens in the evening. Your assistant stays on to reassure, advise and guide customers all the way to checkout.",
    chat: [
      { from: "user", text: "Do you ship to Belgium? I'd like to order tonight.", time: "02:47" },
      { from: "bot", text: "Yes, we ship to Belgium in 3 to 5 business days. You can order right now.", time: "02:47", link: "View my cart" },
      { from: "user", text: "Perfect, checking out.", time: "02:48" },
    ],
    done: "Order placed at 02:49",
  },
  pricing: {
    eyebrow: "Pricing",
    title: "One plan. Everything included.",
    badge: "Launch offer",
    price: "€49",
    per: "/ month",
    setupLabel: "One-time setup fee",
    setupOld: "€499",
    setupNew: "€199",
    noCommit: "No commitment, cancel anytime",
    note: "Reserved for our first partner brands.",
    features: [
      "Assistant connected to your catalog",
      "Size, shipping and returns advice",
      "Callback requests sent by email",
      "Conversation dashboard",
      "Matches your brand",
      "Replies in the customer's language",
      "Adjustments included",
    ],
    cta: "Get my demo",
  },
  contact: {
    eyebrow: "Contact",
    title: "See your assistant before you decide.",
    sub: "Send us your store's address and we'll prepare a personalised demo within 24 hours. Happy to set up a call if you'd like to talk it through.",
    cta: "Get my demo",
    subject: "Replai demo for my store",
    reassurance: ["Free demo", "Reply within 24 h", "No commitment"],
  },
  mascot: {
    day: "Hi! A question about sizing?",
    work: "Answering your customers…",
    evening: "Getting late… I'm still here.",
    night: "Reply sent at 02:47",
  },
  footer: { rights: "All rights reserved" },
};

export const COPY = { fr, en };
