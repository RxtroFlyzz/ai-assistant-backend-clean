import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "hsl(260, 87%, 3%)",
        accent: "#6366f1",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["General Sans", "sans-serif"],
      },
      animation: {
        marquee: "marquee 30s linear infinite",
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
      },
      keyframes: {
        marquee: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      backgroundImage: {
        "hero-glow":
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.25), transparent)",
        "cta-glow":
          "radial-gradient(ellipse 60% 60% at 50% 50%, rgba(99,102,241,0.2), transparent)",
      },
    },
  },
  plugins: [],
};
export default config;
