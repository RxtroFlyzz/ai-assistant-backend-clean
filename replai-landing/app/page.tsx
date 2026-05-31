"use client";

import { LangProvider } from "./context/LangContext";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import HowItWorks from "./components/HowItWorks";
import Features from "./components/Features";
import Pricing from "./components/Pricing";
import CtaSection from "./components/CtaSection";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <LangProvider>
      <div className="min-h-screen" style={{ background: "hsl(260, 87%, 3%)" }}>
        <Navbar />
        <main>
          <Hero />
          <HowItWorks />
          <Features />
          <Pricing />
          <CtaSection />
        </main>
        <Footer />
      </div>
    </LangProvider>
  );
}
