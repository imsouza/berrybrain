/** @type {import('next').NextConfig} */
const assetPrefix = process.env.NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX || "";
const apiOrigin = (process.env.BERRYBRAIN_INTERNAL_API_URL || "http://api:8000").replace(/\/+$/, "");
const configuredProxyTimeout = Number.parseInt(process.env.BERRYBRAIN_PROXY_TIMEOUT_MS || "95000", 10);
const proxyTimeout = Number.isFinite(configuredProxyTimeout) ? configuredProxyTimeout : 95000;

const nextConfig = {
  output: "standalone",
  assetPrefix,
  devIndicators: false,
  typedRoutes: true,
  experimental: {
    // Graph inference may legitimately wait up to 80s for the configured model.
    proxyTimeout,
  },
  images: {
    path: `${assetPrefix}/_next/image`,
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` },
    ];
  },
};

export default nextConfig;
