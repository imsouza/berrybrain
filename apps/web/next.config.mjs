/** @type {import('next').NextConfig} */
const assetPrefix = process.env.NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX || "";
const apiOrigin = (process.env.BERRYBRAIN_INTERNAL_API_URL || "http://api:8000").replace(/\/+$/, "");

const nextConfig = {
  output: "standalone",
  assetPrefix,
  devIndicators: false,
  typedRoutes: true,
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
