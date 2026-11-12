// Mise en page commune des pages juridiques (mentions legales, CGV, confidentialite).
// Un bloc est un paragraphe (texte) ou une liste a puces (tableau de textes).

export type LegalBlock = string | string[];
export type LegalSection = { title: string; blocks: LegalBlock[] };

const PAGES = [
  { href: "/mentions-legales", label: "Mentions légales" },
  { href: "/cgv", label: "Conditions générales de vente" },
  { href: "/confidentialite", label: "Politique de confidentialité" },
];

export default function LegalPage({
  title,
  updated,
  intro,
  sections,
}: {
  title: string;
  updated: string;
  intro?: string;
  sections: LegalSection[];
}) {
  return (
    <div className="min-h-screen text-slate-200" style={{ background: "hsl(260, 87%, 3%)" }}>
      <header className="mx-auto flex w-full max-w-3xl items-center justify-between px-5 py-6 sm:px-8">
        <a href="/" className="flex items-center gap-2 font-display text-lg font-semibold text-white">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 text-sm">
            R
          </span>
          Replai
        </a>
        <a href="/" className="text-sm text-slate-400 transition-colors hover:text-white">
          Retour au site
        </a>
      </header>

      <main className="mx-auto w-full max-w-3xl px-5 pb-24 pt-6 sm:px-8">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-white sm:text-4xl">{title}</h1>
        <p className="mt-3 text-sm text-slate-500">Dernière mise à jour : {updated}</p>
        {intro && <p className="mt-6 leading-relaxed text-slate-300">{intro}</p>}

        {sections.map((s, i) => (
          <section key={s.title} className="mt-10">
            <h2 className="font-display text-xl font-semibold text-white">
              {i + 1}. {s.title}
            </h2>
            {s.blocks.map((b, j) =>
              Array.isArray(b) ? (
                <ul key={j} className="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-slate-300 marker:text-slate-600">
                  {b.map((item, k) => (
                    <li key={k}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p key={j} className="mt-3 leading-relaxed text-slate-300">
                  {b}
                </p>
              )
            )}
          </section>
        ))}

        <nav className="mt-16 flex flex-wrap gap-x-6 gap-y-2 border-t border-white/10 pt-6 text-sm">
          {PAGES.map((p) => (
            <a key={p.href} href={p.href} className="text-slate-400 transition-colors hover:text-white">
              {p.label}
            </a>
          ))}
        </nav>
      </main>
    </div>
  );
}
