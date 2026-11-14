"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", label: "confirmations" },
  { href: "/contested", label: "contested" },
  { href: "/bridges", label: "bridges" },
  { href: "/mediated", label: "mediated" },
  { href: "/caveats", label: "caveats" },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <nav className="flex gap-5 sm:gap-7">
      {tabs.map((t) => {
        const active = pathname === t.href;
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={active ? "page" : undefined}
            className={`label hover:text-ink transition-colors ${
              active ? "text-ink underline underline-offset-4 decoration-1" : ""
            }`}
          >
            {t.label}
          </Link>
        );
      })}
    </nav>
  );
}
