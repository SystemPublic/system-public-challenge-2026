import type { ReactNode } from "react";

type Props = {
  eyebrow?: ReactNode;
  children: ReactNode;
  as?: "h1" | "h2" | "h3";
  lede?: ReactNode;
  id?: string;
  className?: string;
};

export function SectionHeading({ eyebrow, children, as = "h2", lede, id, className = "" }: Props) {
  const Tag = as;
  const size =
    as === "h1"
      ? "text-4xl sm:text-6xl"
      : as === "h2"
        ? "text-3xl sm:text-4xl"
        : "text-xl sm:text-2xl";
  return (
    <div className={`max-w-3xl ${className}`}>
      {eyebrow ? (
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-muted">{eyebrow}</p>
      ) : null}
      <Tag id={id} className={`font-display font-semibold tracking-tight text-balance ${size}`}>
        {children}
      </Tag>
      {lede ? <p className="mt-4 text-lg text-muted text-pretty">{lede}</p> : null}
    </div>
  );
}
