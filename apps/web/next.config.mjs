/** @type {import('next').NextConfig} */
const assetPrefix = process.env.NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX || "";

const nextConfig = {
  assetPrefix,
  devIndicators: false,
  typedRoutes: true,
  images: {
    path: `${assetPrefix}/_next/image`,
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://api:8000/api/:path*" },
    ];
  },
};

export default nextConfig;
