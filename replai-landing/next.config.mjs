/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "d8j0ntlcm91z4.cloudfront.net",
      },
    ],
  },
  // Allow the CloudFront video to load without CSP issues
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; " +
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
              "style-src 'self' 'unsafe-inline' https://api.fontshare.com; " +
              "font-src 'self' https://api.fontshare.com; " +
              "media-src 'self' https://d8j0ntlcm91z4.cloudfront.net; " +
              "img-src 'self' data: blob: https:; " +
              "connect-src 'self';",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
