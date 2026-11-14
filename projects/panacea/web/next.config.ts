import type { NextConfig } from "next";
import createMDX from "@next/mdx";

const nextConfig: NextConfig = {
  pageExtensions: ["js", "jsx", "md", "mdx", "ts", "tsx"],
  cacheComponents: true,
  partialPrefetching: true,
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
