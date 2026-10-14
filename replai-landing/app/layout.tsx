import type { Metadata } from "next";
import ReplaiWidget from "./components/ReplaiWidget";
import "./globals.css";

export const metadata: Metadata = {
  title: "Replai — L'assistant IA des boutiques en ligne",
  description:
    "Replai répond à vos clients à toute heure : tailles, stocks, livraison, retours. Moins de ventes perdues, moins de messages à traiter.",
  metadataBase: new URL("https://aireply.fr"),
  openGraph: {
    title: "Replai — L'assistant IA des boutiques en ligne",
    description: "Vos clients ont des questions. Même à 3 h du matin.",
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
      <body className="antialiased">
        {children}
        <ReplaiWidget />
      </body>
    </html>
  );
}
