import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
      {
        source: "/static/:path*",
        destination: "http://localhost:8001/static/:path*",
      }
    ];
  },
};

export default nextConfig;
