"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export const NAV = [
  { href: "/", label: "Map", match: ["/", "/map"] },
  { href: "/board", label: "Patients", match: ["/board"] },
  { href: "/medicines", label: "Medicines", match: ["/medicines", "/drug"] },
  { href: "/phone", label: "Patient app", match: ["/phone"] },
];

const isOn = (path: string, m: string[]) => m.some((p) => (p === "/" ? path === "/" : path === p || path.startsWith(p + "/")));

export function NavLinks({ path }: { path: string | null }) {
  return (
    <nav aria-label="Main" className="-mx-2 flex flex-wrap text-[15px]">
      {NAV.map((n) => {
        const on = path !== null && isOn(path, n.match);
        return (
          <Link
            key={n.href}
            href={n.href}
            aria-current={on ? "page" : undefined}
            className={`px-2 py-1 sm:px-3 ${
              on ? "font-semibold text-ink underline decoration-2 underline-offset-[10px]" : "text-ink-muted hover:text-ink"
            }`}
          >
            {n.label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Highlights the current tab. Must sit inside <Suspense> (usePathname with Cache Components). */
export function ActiveNav() {
  return <NavLinks path={usePathname() ?? "/"} />;
}
