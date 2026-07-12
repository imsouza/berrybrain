/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: "/berrybrain",
  devIndicators: false,
  typedRoutes: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://api:8000/api/:path*" },
    ];
  },
};

export default nextConfig;
