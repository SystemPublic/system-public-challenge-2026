import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import Link from "next/link";
import { Disclaimer } from "@/components/Disclaimer";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cool-Aid",
  description: "Medications and heat: a clinician tool, a public story and a patient app. Prototype.",
};

// App font (Rachel, Sat 14 Nov): Plus Jakarta Sans, self-hosted by next/font (works offline).
// Exposed as --font-jakarta; tokens.css puts it first in --font-body.
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin", "latin-ext"], variable: "--font-jakarta", display: "swap" });

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={jakarta.variable}>
      <body className="min-h-screen antialiased">
        <SiteHeader />
        <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
        <footer className="mx-auto mt-8 max-w-7xl border-t border-line px-4 py-6">
          <Disclaimer className="text-xs" />
          <p className="mt-1 text-xs text-ink-muted">
            Built on the System public graph, peer-reviewed literature and FDA reports. Every claim links to its source.
            Patients shown are synthetic.{" "}
            <Link href="/evidence" className="underline">
              Methods
            </Link>
          </p>
        </footer>
      </body>
    </html>
  );
}
