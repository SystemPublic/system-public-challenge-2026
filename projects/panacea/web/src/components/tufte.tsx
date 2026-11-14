// Tufte-style authoring components, usable directly inside MDX.
// All server components: the sidenote toggle below `lg` is pure CSS
// (Tufte's checkbox pattern), zero client JS.

import { useId } from "react";

export function Sidenote({
  n,
  children,
}: {
  /** Footnote number, unique per page (Tufte CSS convention). */
  n: number;
  children: React.ReactNode;
}) {
  const id = `sn-${n}-${useId()}`;
  return (
    <>
      <label className="margin-toggle sidenote-number" htmlFor={id}>
        {n}
      </label>
      <input type="checkbox" id={id} className="margin-toggle" />
      <span className="sidenote">
        <span className="sn-num">{n}</span> {children}
      </span>
    </>
  );
}

export function MarginNote({ children }: { children: React.ReactNode }) {
  const id = `mn-${useId()}`;
  return (
    <>
      <label className="margin-toggle" htmlFor={id}>
        ⊕
      </label>
      <input type="checkbox" id={id} className="margin-toggle" />
      <span className="marginnote">{children}</span>
    </>
  );
}

export function Figure({
  src,
  alt,
  caption,
  wide = false,
  margin = false,
}: {
  src: string;
  alt: string;
  caption?: string;
  /** Break out into the margin column (full width). */
  wide?: boolean;
  /** Live entirely in the margin, like a large margin note. */
  margin?: boolean;
}) {
  return (
    <figure className={wide ? "fullwidth" : margin ? "marginfig" : undefined}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} loading="lazy" />
      {caption && <figcaption>{caption}</figcaption>}
    </figure>
  );
}

export function FullWidth({ children }: { children: React.ReactNode }) {
  return <figure className="fullwidth">{children}</figure>;
}

export function Epigraph({
  children,
  cite,
}: {
  children: React.ReactNode;
  cite?: string;
}) {
  return (
    <blockquote className="epigraph">
      <p>{children}</p>
      {cite && <footer>{cite}</footer>}
    </blockquote>
  );
}

export function Newthought({ children }: { children: React.ReactNode }) {
  return <span className="newthought">{children}</span>;
}

/** Self-contained HTML/JS demo served from /public, embedded in an iframe. */
export function Demo({
  src,
  caption,
  title,
}: {
  src: string;
  caption?: string;
  title: string;
}) {
  return (
    <figure>
      <div className="iframe-wrapper">
        <iframe src={src} title={title} loading="lazy" />
      </div>
      {caption && <figcaption>{caption}</figcaption>}
    </figure>
  );
}
