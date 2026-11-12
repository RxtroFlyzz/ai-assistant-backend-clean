import type { Metadata } from "next";
import LegalPage, { LegalSection } from "../components/LegalPage";

export const metadata: Metadata = {
  title: "Mentions légales · Replai",
  description: "Éditeur, hébergeurs et contact du site aireply.fr.",
};

const sections: LegalSection[] = [
  {
    title: "Éditeur du site",
    blocks: [
      "Le site aireply.fr et le service Replai sont édités par :",
      [
        "Gianluca Ferlin, entrepreneur individuel (EI), exerçant sous le nom commercial « Replai »",
        "Adresse : 15 allée des Érables, 78670 Villennes-sur-Seine, France",
        "SIRET : en cours d'attribution (entreprise en cours d'immatriculation)",
        "TVA non applicable, art. 293 B du code général des impôts",
        "Email : contact@aireply.fr",
        "Téléphone : +33 7 82 97 77 46",
      ],
      "Directeur de la publication : Gianluca Ferlin.",
    ],
  },
  {
    title: "Hébergement",
    blocks: [
      [
        "Site aireply.fr : Vercel Inc., 440 N Barranca Avenue #4133, Covina, CA 91723, États-Unis (vercel.com)",
        "Service Replai (assistant, tableau de bord, base de données) : Render Services, Inc., 525 Brannan Street, Suite 300, San Francisco, CA 94107, États-Unis (render.com)",
        "Nom de domaine : OVH SAS, 2 rue Kellermann, 59100 Roubaix, France (ovhcloud.com)",
      ],
    ],
  },
  {
    title: "Propriété intellectuelle",
    blocks: [
      "Le site, ses textes, ses visuels, la marque Replai et le logiciel de l'assistant sont protégés par le droit de la propriété intellectuelle. Toute reproduction ou réutilisation sans accord écrit préalable est interdite.",
      "Les conversations d'exemple affichées sur le site mettent en scène une boutique fictive, « Maison Nuage ». Les articles qui y figurent n'existent pas et ne sont pas à vendre.",
    ],
  },
  {
    title: "Assistant IA",
    blocks: [
      "L'assistant présent sur ce site, comme ceux installés sur les boutiques de nos clients, est un système d'intelligence artificielle : ses réponses sont générées automatiquement et peuvent contenir des erreurs. Pour toute information engageante (prix, délais, conditions), les conditions affichées sur la boutique concernée font foi.",
      "Vous pouvez à tout moment demander à être recontacté par une personne, avec le bouton « Parler à un humain ».",
    ],
  },
  {
    title: "Données personnelles",
    blocks: [
      "Le traitement de vos données est décrit dans notre politique de confidentialité, accessible à l'adresse aireply.fr/confidentialite.",
    ],
  },
  {
    title: "Contact",
    blocks: ["Pour toute question ou signalement concernant le site : contact@aireply.fr."],
  },
];

export default function Page() {
  return <LegalPage title="Mentions légales" updated="12 novembre 2026" sections={sections} />;
}
