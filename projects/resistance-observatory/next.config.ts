import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The landing experience is public/story.html. This answers "/" with a real
  // redirect before any page renders; app/page.tsx does the same as a fallback.
  async redirects() {
    return [{ source: "/", destination: "/story.html", permanent: false }];
  },
};

export default nextConfig;
