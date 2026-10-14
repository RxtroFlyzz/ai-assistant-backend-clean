"use client";

import { LangProvider } from "./context/LangContext";
import SkyScene from "./components/SkyScene";
import Mascot from "./components/Mascot";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Benefits from "./components/Benefits";
import HowItWorks from "./components/HowItWorks";
import Features from "./components/Features";
import NightShift from "./components/NightShift";
import Pricing from "./components/Pricing";
import Contact from "./components/Contact";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <LangProvider>
      <SkyScene>
        <Navbar />
        <main>
          <Hero />
          <Benefits />
          <HowItWorks />
          <Features />
          <NightShift />
          <Pricing />
          <Contact />
        </main>
        <Footer />
        <Mascot />
      </SkyScene>
    </LangProvider>
  );
}
