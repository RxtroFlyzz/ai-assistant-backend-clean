import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://aireply.fr",
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    ...["mentions-legales", "cgv", "confidentialite"].map((page) => ({
      url: "https://aireply.fr/" + page,
      lastModified: new Date(),
      changeFrequency: "yearly" as const,
      priority: 0.2,
    })),
  ];
}
