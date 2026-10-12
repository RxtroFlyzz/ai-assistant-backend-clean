import type { Metadata } from "next";
import Script from "next/script";

// Page de demo privee envoyee aux prospects :
//   https://aireply.fr/demo?token=<token_client>&name=<Nom de la marque>
// Elle charge le widget du prospect (avec son vrai catalogue) a la place de
// celui de Replai, et n'est pas indexee par Google.

const WIDGET_URL = "https://ai-assistant-backend-clean-iz6y.onrender.com/static/ai-widget.js";
const TOKEN_RE = /^[A-Za-z0-9_-]{3,80}$/;

type Props = { searchParams: { token?: string; name?: string } };

function cleanName(raw?: string): string {
  const name = (raw || "").trim().slice(0, 60);
  return name || "votre boutique";
}

export function generateMetadata({ searchParams }: Props): Metadata {
  return {
    title: "Démo privée · " + cleanName(searchParams.name) + " · Replai",
    robots: { index: false, follow: false },
  };
}

const EXEMPLES = [
  "Vous l'avez en taille M ?",
  "C'est livré en combien de temps ?",
  "Je peux le retourner s'il ne me va pas ?",
  "Je veux parler à quelqu'un",
];

export default function DemoPage({ searchParams }: Props) {
  const token = searchParams.token || "";
  const valid = TOKEN_RE.test(token);
  const name = cleanName(searchParams.name);

  return (
    <div
      className="min-h-screen text-white flex flex-col"
      style={{ background: "hsl(260, 87%, 3%)" }}
    >
      <div className="pointer-events-none fixed inset-0 bg-hero-glow" />

      <header className="relative px-4 sm:px-6 py-5 flex items-center justify-between max-w-5xl w-full mx-auto">
        <a href="/" className="flex items-center gap-2 font-display font-semibold text-lg">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-sm">
            R
          </span>
          Replai
        </a>
        <span className="text-xs uppercase tracking-widest text-indigo-300/80 border border-indigo-400/30 rounded-full px-3 py-1">
          Démo privée
        </span>
      </header>

      <main className="relative flex-1 flex items-center px-4 sm:px-6 pb-28">
        <div className="max-w-2xl mx-auto w-full">
          {valid ? (
            <>
              <h1 className="font-display text-3xl sm:text-5xl font-semibold leading-tight">
                L&apos;assistant IA de{" "}
                <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-amber-300 bg-clip-text text-transparent">
                  {name}
                </span>
              </h1>
              <p className="mt-5 text-base sm:text-lg text-slate-300 leading-relaxed">
                Il connaît déjà votre catalogue, vos prix et vos stocks par taille, mis à jour
                automatiquement. Testez-le comme le ferait un de vos clients : ouvrez la bulle
                en bas à droite de l&apos;écran.
              </p>

              <div className="mt-8">
                <p className="text-sm text-slate-400 mb-3">Quelques questions à essayer :</p>
                <div className="flex flex-wrap gap-2">
                  {EXEMPLES.map((q) => (
                    <span
                      key={q}
                      className="text-sm text-slate-200 bg-white/5 border border-white/10 rounded-full px-4 py-2"
                    >
                      {q}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-10 grid sm:grid-cols-2 gap-3">
                <div className="rounded-2xl bg-white/5 border border-white/10 p-5">
                  <p className="font-semibold">Répond 24h/24</p>
                  <p className="mt-1 text-sm text-slate-400">
                    Tailles, livraison, retours : vos clients ont une réponse tout de suite,
                    même la nuit.
                  </p>
                </div>
                <div className="rounded-2xl bg-white/5 border border-white/10 p-5">
                  <p className="font-semibold">Ne perd aucun client</p>
                  <p className="mt-1 text-sm text-slate-400">
                    Quand un client laisse ses coordonnées, vous recevez un email et il apparaît
                    dans votre tableau de bord.
                  </p>
                </div>
              </div>

              <a
                href="/#contact"
                className="mt-10 inline-flex items-center gap-2 px-7 py-3.5 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-amber-400 font-semibold shadow-xl shadow-indigo-500/30 hover:scale-105 transition-transform"
              >
                L&apos;installer sur ma boutique →
              </a>
            </>
          ) : (
            <>
              <h1 className="font-display text-3xl sm:text-4xl font-semibold">Lien de démo invalide</h1>
              <p className="mt-4 text-slate-300">
                Ce lien est incomplet ou a expiré. Demandez un nouveau lien à la personne qui
                vous l&apos;a envoyé, ou découvrez Replai sur{" "}
                <a href="/" className="underline text-indigo-300">aireply.fr</a>.
              </p>
            </>
          )}
        </div>
      </main>

      {valid && (
        <>
          <div className="fixed bottom-7 right-24 hidden sm:flex items-center gap-2 text-sm text-indigo-200/80 pointer-events-none">
            Essayez ici
            <span aria-hidden className="text-xl">→</span>
          </div>
          <Script src={WIDGET_URL + "?token=" + encodeURIComponent(token)} strategy="afterInteractive" />
        </>
      )}
    </div>
  );
}
