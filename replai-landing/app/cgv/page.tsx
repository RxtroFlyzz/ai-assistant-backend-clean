import type { Metadata } from "next";
import LegalPage, { LegalSection } from "../components/LegalPage";

export const metadata: Metadata = {
  title: "Conditions générales de vente · Replai",
  description: "Conditions de vente du service Replai : prix, paiement, résiliation, données.",
};

const sections: LegalSection[] = [
  {
    title: "Objet",
    blocks: [
      "Les présentes conditions générales de vente (CGV) s'appliquent à toute commande du service Replai passée auprès de Gianluca Ferlin, entrepreneur individuel (EI), ci-après « Replai », par un professionnel exploitant une boutique en ligne, ci-après « le Client ».",
      "Le service est réservé aux professionnels. Toute commande vaut acceptation des présentes CGV, qui prévalent sur tout autre document du Client.",
    ],
  },
  {
    title: "Le service",
    blocks: [
      "Replai fournit un assistant conversationnel fondé sur l'intelligence artificielle, installé sur la boutique en ligne du Client. Le service comprend :",
      [
        "un assistant qui répond aux visiteurs à partir du catalogue de la boutique (produits, prix, stocks, tailles) et de ses conditions de livraison et de retour ;",
        "la transmission par email des coordonnées des visiteurs qui demandent à être recontactés ;",
        "un tableau de bord donnant accès aux conversations, aux demandes de rappel et aux statistiques ;",
        "la mise aux couleurs de la marque et les ajustements raisonnables de l'assistant.",
      ],
      "Le service est aujourd'hui proposé pour les boutiques Shopify. Toute autre plateforme doit faire l'objet d'un accord préalable.",
      "L'assistant est un système d'intelligence artificielle : ses réponses sont générées automatiquement et peuvent contenir des erreurs. Replai s'engage à apporter tout le soin nécessaire à sa configuration, sans garantir l'exactitude de chaque réponse ni un résultat commercial.",
    ],
  },
  {
    title: "Démo et commande",
    blocks: [
      "Replai prépare gratuitement, sans engagement, une démonstration personnalisée de l'assistant sur la boutique du Client.",
      "La commande est formée lorsque le Client confirme par écrit (email) qu'il souhaite souscrire au service et règle les frais de mise en place. Replai installe ensuite l'assistant, ou communique au Client le code à ajouter à sa boutique.",
    ],
  },
  {
    title: "Prix",
    blocks: [
      [
        "Abonnement : 49 € par mois, tout inclus.",
        "Frais de mise en place : 199 €, payés une seule fois (offre de lancement, au lieu de 499 €).",
      ],
      "TVA non applicable, art. 293 B du code général des impôts.",
      "Replai peut modifier le prix de l'abonnement en prévenant le Client par email au moins 30 jours à l'avance. Le Client qui refuse le nouveau prix peut résilier avant son entrée en vigueur.",
    ],
  },
  {
    title: "Facturation et paiement",
    blocks: [
      "Les frais de mise en place sont facturés à la commande. L'abonnement est facturé chaque mois, d'avance, à compter de la mise en ligne de l'assistant.",
      "Le paiement se fait par prélèvement SEPA ou par virement, dans un délai de 15 jours à compter de la date de la facture.",
      "Tout retard de paiement entraîne de plein droit, sans rappel préalable, des pénalités calculées au taux de trois fois le taux d'intérêt légal, ainsi qu'une indemnité forfaitaire pour frais de recouvrement de 40 €.",
    ],
  },
  {
    title: "Suspension en cas d'impayé",
    blocks: [
      "Si une facture reste impayée 15 jours après une relance par email, Replai peut suspendre l'assistant jusqu'au règlement complet des sommes dues. L'abonnement reste dû pendant la suspension.",
      "Si l'impayé persiste 30 jours après la suspension, Replai peut résilier le contrat de plein droit, sans préjudice des sommes restant dues.",
    ],
  },
  {
    title: "Durée et résiliation",
    blocks: [
      "Le contrat est conclu sans engagement, pour une durée indéterminée.",
      "Le Client peut résilier à tout moment, sans motif, par email à contact@aireply.fr. La résiliation prend effet sous un jour ouvré : l'assistant est alors désactivé et plus aucun abonnement n'est facturé. Le mois en cours reste dû et n'est pas remboursé au prorata.",
      "Replai peut résilier le contrat en prévenant le Client 30 jours à l'avance, ou sans préavis en cas de manquement grave du Client (notamment un usage illicite du service).",
    ],
  },
  {
    title: "Frais de mise en place",
    blocks: [
      "Les frais de mise en place rémunèrent le travail de configuration de l'assistant. Ils ne sont pas remboursables une fois l'assistant mis en ligne, y compris si le Client résilie ensuite.",
      "Ils sont intégralement remboursés si Replai ne parvient pas à mettre l'assistant en ligne sur la boutique du Client.",
    ],
  },
  {
    title: "Droit de rétractation des petits professionnels",
    blocks: [
      "Lorsque la loi lui reconnaît ce droit (contrat conclu à distance, objet n'entrant pas dans le champ de son activité principale, cinq salariés au plus), le Client dispose de 14 jours à compter de la commande pour se rétracter, par email à contact@aireply.fr.",
      "En passant commande, le Client demande expressément que la mise en place commence sans attendre la fin de ce délai. Il reconnaît qu'il ne pourra plus se rétracter des frais de mise en place une fois l'assistant mis en ligne avec son accord. S'il se rétracte de l'abonnement dans le délai de 14 jours, il ne doit que la part correspondant à la période pendant laquelle le service a été fourni.",
    ],
  },
  {
    title: "Engagements du Client",
    blocks: [
      [
        "fournir des informations exactes et tenir à jour le catalogue et les conditions de sa boutique, sur lesquels l'assistant s'appuie ;",
        "vérifier les réponses de l'assistant lors de la mise en place et signaler toute erreur à Replai ;",
        "informer ses visiteurs de l'utilisation d'un assistant IA et mentionner le service dans sa propre politique de confidentialité ;",
        "ne pas utiliser le service à des fins illicites, trompeuses ou contraires aux droits des tiers ;",
        "garder confidentiel le mot de passe de son tableau de bord.",
      ],
      "Le Client reste seul responsable de sa boutique, de ses produits, de ses prix et de ses relations avec ses propres clients.",
    ],
  },
  {
    title: "Données personnelles",
    blocks: [
      "Pour les conversations de ses visiteurs, le Client est responsable de traitement et Replai agit comme sous-traitant, au sens du règlement général sur la protection des données (RGPD). À ce titre, Replai :",
      [
        "ne traite ces données que pour fournir le service, sur instruction du Client ;",
        "veille à leur confidentialité et à leur sécurité ;",
        "fait appel aux sous-traitants ultérieurs listés dans sa politique de confidentialité (hébergement, génération des réponses, envoi des emails) et informe le Client de tout changement ;",
        "aide le Client à répondre aux demandes des personnes concernées (accès, rectification, effacement) ;",
        "prévient le Client dans les meilleurs délais en cas de violation de données ;",
        "conserve les conversations et les coordonnées 12 mois au plus, et supprime les données du Client dans les 30 jours suivant la fin du contrat.",
      ],
      "Le détail des traitements figure dans la politique de confidentialité, accessible à l'adresse aireply.fr/confidentialite.",
    ],
  },
  {
    title: "Propriété intellectuelle",
    blocks: [
      "Replai reste propriétaire du logiciel, de l'assistant et de leur documentation. Le Client dispose d'un droit d'utilisation personnel et non exclusif pendant la durée du contrat.",
      "Le Client reste propriétaire de ses contenus, de son catalogue et des données de ses visiteurs. Replai ne cite le Client comme référence qu'avec son accord.",
    ],
  },
  {
    title: "Disponibilité et responsabilité",
    blocks: [
      "Replai met en œuvre les moyens raisonnables pour assurer la disponibilité du service, sans garantir un fonctionnement ininterrompu. Le service dépend de prestataires tiers (hébergement, modèles d'intelligence artificielle, plateforme de la boutique) dont Replai ne maîtrise pas les interruptions.",
      "Replai n'est pas responsable des dommages indirects, notamment la perte de chiffre d'affaires, ni des conséquences d'une réponse erronée de l'assistant. Sa responsabilité est en tout état de cause limitée aux sommes payées par le Client au cours des douze derniers mois.",
      "Aucune partie n'est responsable d'un manquement dû à un cas de force majeure.",
    ],
  },
  {
    title: "Modification des CGV",
    blocks: [
      "Replai peut modifier les présentes CGV en prévenant le Client par email au moins 30 jours à l'avance. Le Client qui refuse les nouvelles conditions peut résilier avant leur entrée en vigueur.",
    ],
  },
  {
    title: "Droit applicable et litiges",
    blocks: [
      "Les présentes CGV sont soumises au droit français. En cas de litige, les parties recherchent d'abord une solution amiable. À défaut, le litige relève des tribunaux compétents du ressort de Versailles.",
    ],
  },
];

export default function Page() {
  return (
    <LegalPage
      title="Conditions générales de vente"
      updated="12 novembre 2026"
      intro="Ces conditions encadrent l'abonnement au service Replai. Elles sont volontairement courtes : pour toute question, écrivez à contact@aireply.fr."
      sections={sections}
    />
  );
}
