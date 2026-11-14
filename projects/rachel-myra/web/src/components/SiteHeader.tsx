import Link from "next/link";
import { Suspense } from "react";
import { DISCLAIMER } from "./Disclaimer";
import { ActiveNav, NavLinks } from "./SiteNav";

export function SiteHeader() {
  return (
    <header className="border-b border-line bg-page">
      <p className="border-b border-line bg-surface px-4 py-1 text-center text-xs text-ink-muted">{DISCLAIMER}</p>
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-3">
        <Link href="/" className="inline-flex items-center gap-2 text-xl font-extrabold tracking-tight" style={{ color: "var(--bucket-store-solid, #0e7c86)" }}>
          {/* Hot-and-cool pill mark (same as app/icon.svg, the tab icon) */}
          <svg viewBox="0 0 64 64" className="h-7 w-7" aria-hidden>
            <g transform="rotate(-45 32 32)">
              <rect x="6" y="19" width="52" height="26" rx="13" fill="#0e7c86" />
              <path d="M19 19h13v26H19a13 13 0 0 1 0-26z" fill="#d55e00" />
              <rect x="31" y="19" width="2" height="26" fill="#ffffff" />
            </g>
          </svg>
          Cool-Aid
        </Link>
        <Suspense fallback={<NavLinks path={null} />}>
          <ActiveNav />
        </Suspense>
      </div>
    </header>
  );
}
