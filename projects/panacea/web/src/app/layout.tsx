import type { Metadata } from "next";
import { EB_Garamond, Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { site } from "@/lib/site";
import { NavLinks } from "@/components/nav-links";
import "./globals.css";

const ebGaramond = EB_Garamond({
  variable: "--font-ebgaramond",
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  display: "swap",
});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: site.title,
    template: `%s · ${site.title}`,
  },
  description: site.description,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${ebGaramond.variable} ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-serif bg-paper text-ink">
        <header className="mx-auto w-full max-w-[72rem] flex items-baseline justify-between px-6 sm:px-10 pt-5 pb-4">
          <Link
            href="/"
            className="font-sans text-[11px] tracking-[0.18em] uppercase text-ink no-underline"
          >
            {site.title}&nbsp;/
          </Link>
          <NavLinks />
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
