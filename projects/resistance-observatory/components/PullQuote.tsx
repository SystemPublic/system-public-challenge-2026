import type { ReactNode } from "react";

export function PullQuote({ children, cite }: { children: ReactNode; cite?: string }) {
  return (
    <figure className="my-14 border-l-4 border-drug pl-6 sm:-mx-10 sm:pl-10">
      <blockquote className="font-display text-3xl font-medium leading-tight tracking-tight text-balance sm:text-4xl">
        <span aria-hidden className="mr-1 text-drug">&ldquo;</span>
        {children}
        <span aria-hidden className="text-drug">&rdquo;</span>
      </blockquote>
      {cite ? <figcaption className="mt-4 font-mono text-xs uppercase tracking-[0.16em] text-muted">— {cite}</figcaption> : null}
    </figure>
  );
}
