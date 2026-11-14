import Link from "next/link";

/** Hero: the problem in one sentence (wording from docs/SCIENCE.md). */
export function Hero({ learnHref }: { learnHref: string }) {
  return (
    <section
      aria-labelledby="hero-h"
      className="relative isolate flex min-h-[calc(100dvh-57px)] items-center overflow-hidden"
    >
      <Backdrop />
      <div className="mx-auto w-full max-w-6xl px-4 py-24 sm:px-6">
        <p className="mb-6 font-mono text-xs uppercase tracking-[0.2em] text-muted">
          Malaria · drug-resistance markers · evidence
        </p>
        <h1
          id="hero-h"
          className="max-w-5xl font-display text-[clamp(2.6rem,7vw,6.2rem)] font-semibold leading-[0.98] tracking-tight text-balance"
        >
          A researcher tracking a resistance marker has no simple way to know when the
          evidence has <em className="not-italic text-drug">shifted enough to matter.</em>
        </h1>
        <div className="mt-12 flex flex-wrap items-center gap-4">
          <Link
            href={learnHref}
            className="rounded-[5px] bg-drug px-6 py-3 font-bold text-bg transition-transform hover:-translate-y-0.5"
          >
            Start with one marker →
          </Link>
          <a href="#scale" className="text-muted underline decoration-line-strong underline-offset-4 hover:text-fg">
            or scroll the story ↓
          </a>
        </div>
      </div>
    </section>
  );
}

/** Original backdrop: an observatory lens — slow rotating rings and a sweep. */
function Backdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
      <svg
        viewBox="0 0 1200 1200"
        preserveAspectRatio="xMidYMid slice"
        className="absolute -right-[30%] top-1/2 h-[150%] w-[130%] -translate-y-1/2 opacity-70 md:-right-[20%]"
      >
        <defs>
          <radialGradient id="ro-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--drug)" stopOpacity="0.14" />
            <stop offset="70%" stopColor="var(--drug)" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="ro-sweep-g" x1="0" x2="1">
            <stop offset="0" stopColor="var(--drug)" stopOpacity="0" />
            <stop offset="1" stopColor="var(--drug)" stopOpacity="0.16" />
          </linearGradient>
        </defs>
        <circle cx="600" cy="600" r="560" fill="url(#ro-glow)" />
        <g className="ro-spin">
          <circle cx="600" cy="600" r="520" fill="none" stroke="var(--line-strong)" strokeWidth="1" strokeDasharray="2 14" />
          <circle cx="600" cy="600" r="380" fill="none" stroke="var(--line)" strokeWidth="1" />
        </g>
        <g className="ro-spin-rev">
          <circle cx="600" cy="600" r="450" fill="none" stroke="var(--line)" strokeWidth="1" strokeDasharray="40 18 4 18" />
          <circle cx="600" cy="600" r="250" fill="none" stroke="var(--line-strong)" strokeWidth="1" strokeDasharray="1 9" />
        </g>
        <path className="ro-sweep" d="M600 600 L1120 600 A520 520 0 0 0 1050 340 Z" fill="url(#ro-sweep-g)" />
        <path d="M600 60v120M600 1020v120M60 600h120M1020 600h120" stroke="var(--line-strong)" strokeWidth="1" />
        <circle cx="600" cy="600" r="6" fill="var(--drug)" />
      </svg>
      <div className="absolute inset-0 bg-gradient-to-r from-bg via-bg/80 to-transparent" />
    </div>
  );
}
