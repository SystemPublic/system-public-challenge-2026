import type { MDXComponents } from "mdx/types";
import {
  Sidenote,
  MarginNote,
  Figure,
  FullWidth,
  Epigraph,
  Newthought,
  Demo,
} from "@/components/tufte";

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    ...components,
    Sidenote,
    MarginNote,
    Figure,
    FullWidth,
    Epigraph,
    Newthought,
    Demo,
  };
}
