"use client";

import Script from "next/script";
import { usePathname } from "next/navigation";

// Widget Replai du site aireply.fr (dogfooding).
// Desactive sur /demo : cette page charge le widget du prospect a la place.
export default function ReplaiWidget() {
  const pathname = usePathname();
  if (pathname?.startsWith("/demo")) return null;
  return (
    <Script
      src="https://ai-assistant-backend-clean-iz6y.onrender.com/static/ai-widget.js?token=replai_cb23fd"
      strategy="afterInteractive"
    />
  );
}
