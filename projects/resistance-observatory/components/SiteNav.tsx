"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useSelection } from "@/lib/selection";

export const NAV_ITEMS = [
  // The story is a standalone HTML page outside the app shell.
  { href: "/story.html", label: "Home" },
  { href: "/overview", label: "Overview" },
  { href: "/learn", label: "Learn" },
  { href: "/forecast", label: "Map" },
  { href: "/alert", label: "Alert" },
  { href: "/data", label: "Data" },
] as const;

/**
 * Same bar as the story page (public/story.html): fixed, circular mark,
 * uppercase letter-spaced wordmark, a pill-outlined link at the right, and the
 * same scroll behaviour — transparent at the top, solid and blurred after 40px.
 * Styles live in globals.css under ".ro-nav".
 */
export function SiteNav() {
  const pathname = usePathname();
  const { hrefWithSelection, markerId } = useSelection();
  const [on, setOn] = useState(false);

  useEffect(() => {
    const read = () => setOn(window.scrollY > 40);
    read();
    window.addEventListener("scroll", read, { passive: true });
    return () => window.removeEventListener("scroll", read);
  }, []);

  return (
    <header>
      <nav aria-label="Primary" className="ro-nav" data-on={on ? "true" : "false"}>
        {/* Plain anchor: the story is a static file, so this is a full page load. */}
        <a href="/story.html" className="ro-nav-brand">
          <span className="ro-nav-symbol" aria-hidden>
            ⌁
          </span>
          <span className="ro-nav-word">
            Resistance <i>Observatory</i>
          </span>
        </a>
        <div className="ro-nav-links">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            if (item.href.endsWith(".html")) {
              return (
                <a key={item.href} href={item.href}>
                  {item.label}
                </a>
              );
            }
            return (
              <Link key={item.href} href={hrefWithSelection(item.href)} aria-current={active ? "page" : undefined}>
                {item.label}
              </Link>
            );
          })}
          {markerId ? (
            <Link
              href={hrefWithSelection("/learn")}
              className="ro-nav-end"
              title="Current marker selection (carried across tabs via the URL)"
            >
              {markerId}
            </Link>
          ) : null}
        </div>
      </nav>
    </header>
  );
}
