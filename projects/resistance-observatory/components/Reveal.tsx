"use client";

import type { ReactNode } from "react";
import { useInView } from "@/lib/motion";

/** Fades/slides children in on first scroll into view. Static under reduced motion (CSS). */
export function Reveal({
  children,
  delay = 0,
  className = "",
  as: Tag = "div",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "li" | "section" | "p";
}) {
  const { ref, inView } = useInView<HTMLDivElement>({ threshold: 0.15 });
  return (
    <Tag
      ref={ref as never}
      data-visible={inView ? "true" : "false"}
      style={{ ["--delay" as string]: `${delay}ms` }}
      className={`reveal ${className}`}
    >
      {children}
    </Tag>
  );
}
