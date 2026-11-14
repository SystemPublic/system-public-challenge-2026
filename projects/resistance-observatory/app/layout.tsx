import type { Metadata } from "next";
import { Suspense, type ReactNode } from "react";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { SelectionProvider } from "@/lib/selection";
import { SiteNav } from "@/components/SiteNav";
import { SiteFooter } from "@/components/SiteFooter";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono-face", display: "swap" });

export const metadata: Metadata = {
  title: {
    default: "Resistance Observatory",
    template: "%s · Resistance Observatory",
  },
  description:
    "When does new evidence change the picture for a malaria drug-resistance marker? A hackathon prototype built on a frozen snapshot of the System Public Graph.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body className="min-h-dvh flex flex-col">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:bg-surface focus:px-3 focus:py-2 focus:rounded"
        >
          Skip to content
        </a>
        {/* useSearchParams() in the provider needs a Suspense boundary. */}
        <Suspense fallback={null}>
          <SelectionProvider>
            <SiteNav />
            <main id="main" className="flex-1 pt-[76px] max-[500px]:pt-[65px]">
              {children}
            </main>
            <SiteFooter />
          </SelectionProvider>
        </Suspense>
      </body>
    </html>
  );
}
