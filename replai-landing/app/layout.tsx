import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Replai — Chatbot IA pour TPEs françaises",
  description:
    "Automatisez vos réponses clients 24h/7j avec un chatbot IA entraîné sur votre activité. Setup en 24h.",
  metadataBase: new URL("https://aireply.fr"),
  openGraph: {
    title: "Replai — Chatbot IA pour TPEs françaises",
    description: "Votre client, toujours répondu.",
    url: "https://aireply.fr",
    siteName: "Replai",
    locale: "fr_FR",
    type: "website",
  },
  verification: {
    google: "O2zzvSiz2IhNfBqC01iydAq1xCEC38R-_N596ThciWU",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://api.fontshare.com" />
        <link
          rel="stylesheet"
          href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600,700&f[]=dm-sans@400,500,600&display=swap"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
