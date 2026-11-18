import type { NextConfig } from "next";
import createMDX from "@next/mdx";

// GitHub Pages deploys a static export under the repo path: build with
//   NEXT_OUTPUT=export NEXT_BASE_PATH=/system-public-challenge-2026 pnpm build
// Local dev/build stays untouched when the env vars are unset. PPR
// (cacheComponents + partialPrefetching) is incompatible with static
// export — and every page here is fully static anyway.
const nextConfig: NextConfig = {
  pageExtensions: ["js", "jsx", "md", "mdx", "ts", "tsx"],
  ...(process.env.NEXT_OUTPUT === "export"
    ? {
        output: "export" as NextConfig["output"],
        cacheComponents: false,
        basePath: process.env.NEXT_BASE_PATH,
        trailingSlash: true,
      }
    : { cacheComponents: true, partialPrefetching: true }),
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

const withMDX = createMDX({
  options: {
    remarkPlugins: [["remark-frontmatter", "yaml"], "remark-math", "remark-gfm"],
    rehypePlugins: [["rehype-katex", { strict: false }], "rehype-highlight"],
  },
});

export default withMDX(nextConfig);
