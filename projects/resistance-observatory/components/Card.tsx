import type { HTMLAttributes, ReactNode } from "react";

type CardProps = {
  as?: "div" | "article" | "section" | "li" | "aside";
  tone?: "default" | "drug" | "signal" | "gap";
  children: ReactNode;
} & HTMLAttributes<HTMLElement>;

const TONES = {
  default: "border-line bg-surface",
  drug: "border-drug/40 bg-drug-soft/50",
  signal: "border-signal/40 bg-signal-soft/50",
  gap: "border-gap/40 bg-gap-soft/50",
} as const;

export function Card({ as: Tag = "div", tone = "default", className = "", children, ...rest }: CardProps) {
  return (
    <Tag
      className={`rounded-[var(--radius)] border p-5 shadow-[var(--shadow)] ${TONES[tone]} ${className}`}
      {...rest}
    >
      {children}
    </Tag>
  );
}
