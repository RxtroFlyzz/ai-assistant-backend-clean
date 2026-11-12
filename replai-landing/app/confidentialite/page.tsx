import type { Metadata } from "next";
import LegalPage, { LegalSection } from "../components/LegalPage";

export const metadata: Metadata = {
  title: "Politique de confidentialité · Replai",
  description: "Quelles données Replai traite, pourquoi, combien de temps, et comment exercer vos droits.",
};

const sections: LegalSection[] = [
  {
    title: "Qui est responsable de vos données",
    blocks: [
      "Deux situations sont à distinguer :",
      [
        "Sur le site aireply.fr (formulaire de démo, assistant du site) : le responsable de traitement est Gianluca Ferlin, entrepreneur individuel (EI) exerçant sous le nom « Replai », 15 allée des Érables, 78670 Villennes-sur-Seine, France.",
        "Sur la boutique en ligne d'un client de Replai : le responsable de traitement est cette boutique. Replai agit pour son compte, comme sous-traitant. La politique de confidentialité de la boutique s'applique en priorité ; cette page décrit ce que Replai fait techniquement.",
      ],
      "Contact pour toute question : contact@aireply.fr.",
    ],
  },
  {
    title: "Les données traitées",
    blocks: [
      [
        "Demande de démo (aireply.fr) : adresse de votre boutique, email, et s'ils sont fournis prénom et téléphone.",
        "Conversations avec un assistant : vos messages et les réponses de l'assistant, la date, la langue, l'adresse de la page consultée. Le texte de la page consultée est lu pour répondre à votre question, mais n'est pas conservé.",
        "Coordonnées laissées dans une conversation : prénom, numéro de téléphone ou email, lorsque vous demandez à être recontacté.",
        "Mesure des résultats sur les boutiques clientes : clic vers un produit ou ajout au panier depuis la conversation, et pour une commande passée après une conversation, son numéro et son montant. Ni votre nom, ni votre adresse, ni vos moyens de paiement ne sont transmis à Replai.",
        "Comptes des boutiques clientes : nom de l'entreprise, email de contact, mot de passe du tableau de bord.",
        "Données techniques : adresse IP et journaux de connexion, conservés par nos hébergeurs pour la sécurité du service.",
      ],
      "Ne communiquez pas dans une conversation de données sensibles (santé, moyens de paiement, mots de passe).",
    ],
  },
  {
    title: "Pourquoi ces données sont traitées",
    blocks: [
      [
        "Répondre à votre demande de démo et vous recontacter : mesures prises à votre demande avant un éventuel contrat.",
        "Répondre à vos questions et transmettre votre demande de rappel à la boutique : intérêt légitime de la boutique à assurer son service client, et exécution de votre demande.",
        "Fournir le service aux boutiques clientes (tableau de bord, statistiques, rapport mensuel) : exécution du contrat.",
        "Mesurer ce que l'assistant apporte à la boutique : intérêt légitime de la boutique à évaluer son service.",
        "Assurer la sécurité et corriger les erreurs : intérêt légitime de Replai.",
      ],
      "Vos données ne sont ni vendues, ni utilisées pour de la publicité.",
    ],
  },
  {
    title: "Intelligence artificielle",
    blocks: [
      "L'assistant est un système d'intelligence artificielle. Pour produire une réponse, vos messages et les informations publiques de la boutique (catalogue, conditions) sont envoyés au fournisseur du modèle de langage, OpenAI. Selon les conditions d'OpenAI applicables à son offre pour les entreprises, ces données ne servent pas à entraîner ses modèles.",
      "Les réponses sont générées automatiquement et peuvent contenir des erreurs. Aucune décision produisant des effets juridiques n'est prise par l'assistant. Vous pouvez à tout moment demander à être recontacté par une personne.",
    ],
  },
  {
    title: "Stockage dans votre navigateur",
    blocks: [
      "L'assistant enregistre dans votre navigateur (stockage local) l'identifiant et l'historique de votre conversation, pour que vous la retrouviez en changeant de page. Sur une boutique cliente, un identifiant de conversation est aussi associé à votre panier, afin de savoir qu'une commande fait suite à une conversation.",
      "Replai n'utilise ni cookie publicitaire, ni outil de suivi tiers. Le site aireply.fr n'utilise pas d'outil de mesure d'audience. Vous pouvez effacer le stockage local depuis les réglages de votre navigateur.",
    ],
  },
  {
    title: "Qui reçoit vos données",
    blocks: [
      "Vos données sont accessibles à Replai et, pour les conversations sur une boutique cliente, à cette boutique. Elles sont traitées par les prestataires suivants, pour le seul besoin du service :",
      [
        "Render Services, Inc. (États-Unis) : hébergement du service et de la base de données.",
        "Vercel Inc. (États-Unis) : hébergement du site aireply.fr.",
        "OpenAI (États-Unis) : génération des réponses de l'assistant.",
        "Resend (États-Unis) : envoi des emails (demandes de rappel, rapports).",
        "OVH (France) et Google (messagerie) : nom de domaine et réception des emails adressés à contact@aireply.fr.",
      ],
    ],
  },
  {
    title: "Transferts hors de l'Union européenne",
    blocks: [
      "Plusieurs de ces prestataires sont établis aux États-Unis. Les transferts sont encadrés par le cadre de protection des données UE–États-Unis (Data Privacy Framework) lorsque le prestataire y adhère, ou par les clauses contractuelles types de la Commission européenne.",
    ],
  },
  {
    title: "Durées de conservation",
    blocks: [
      [
        "Conversations et coordonnées laissées dans une conversation : 12 mois au plus.",
        "Demandes de démo : 12 mois au plus après le dernier échange.",
        "Données d'une boutique cliente : supprimées dans les 30 jours suivant la fin du contrat.",
        "Factures et pièces comptables : 10 ans, durée imposée par la loi.",
      ],
    ],
  },
  {
    title: "Vos droits",
    blocks: [
      "Vous pouvez demander l'accès à vos données, leur rectification, leur effacement, la limitation de leur traitement, leur portabilité, ou vous opposer à leur traitement.",
      "Écrivez à contact@aireply.fr : une réponse vous est apportée dans un délai d'un mois. Si votre demande concerne une conversation tenue sur une boutique cliente, vous pouvez aussi vous adresser directement à cette boutique ; Replai l'aide à vous répondre.",
      "Vous pouvez également introduire une réclamation auprès de la CNIL (cnil.fr).",
    ],
  },
  {
    title: "Sécurité",
    blocks: [
      "Les échanges avec le service sont chiffrés (HTTPS). L'accès aux conversations est limité à Replai et à la boutique concernée, dont le tableau de bord est protégé par un mot de passe.",
    ],
  },
  {
    title: "Modification de cette politique",
    blocks: [
      "Cette politique peut évoluer avec le service. La date de dernière mise à jour figure en haut de la page ; les boutiques clientes sont prévenues par email de tout changement important.",
    ],
  },
];

export default function Page() {
  return (
    <LegalPage
      title="Politique de confidentialité"
      updated="12 novembre 2026"
      intro="Cette page explique simplement quelles données Replai traite, pourquoi, pendant combien de temps, et comment exercer vos droits."
      sections={sections}
    />
  );
}
