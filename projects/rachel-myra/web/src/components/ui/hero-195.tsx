"use client";

// Hero in the shadcnblocks "Hero195" style: headline, short subhead, two actions, and a
// tabbed product preview framed by an animated border beam. The preview is the LIVE app
// (the map by default), not stock images or charts: callers pass the tab contents.

import Link from "next/link";
import type { ReactNode } from "react";

import { BorderBeam } from "@/components/ui/border-beam";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export interface Hero195Tab {
  value: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
}

export interface Hero195Props {
  eyebrow?: string;
  title?: string;
  description?: string;
  primary?: { label: string; href: string };
  secondary?: { label: string; href: string };
  tabs: Hero195Tab[];
  defaultTab?: string;
  className?: string;
}

export function Hero195({
  eyebrow = "Heat wave forecast · June 24, 2025 (replay)",
  title = "Who is at risk in the heat, and where to go",
  description = "Each dot is a synthetic patient's home, colored by heat risk from their medicines and their home. Cool places are on the map.",
  primary = { label: "See who to call", href: "/board" },
  secondary = { label: "Open the patient app", href: "/phone" },
  tabs,
  defaultTab,
  className,
}: Hero195Props) {
  return (
    <section className={cn("animate-fade-in", className)}>
      <div className="mx-auto max-w-3xl text-center">
        {eyebrow && <p className="text-sm font-medium text-muted-foreground">{eyebrow}</p>}
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-5xl">{title}</h1>
        {description && <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">{description}</p>}
        <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button asChild size="lg">
            <Link href={primary.href}>{primary.label}</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href={secondary.href}>{secondary.label}</Link>
          </Button>
        </div>
      </div>

      <Tabs defaultValue={defaultTab ?? tabs[0]?.value} className="mt-8">
        {tabs.length > 1 && (
          <div className="flex justify-center">
            <TabsList>
              {tabs.map((t) => (
                <TabsTrigger key={t.value} value={t.value} className="gap-2">
                  {t.icon}
                  {t.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>
        )}
        <div className="relative mt-4 rounded-xl border border-border bg-card p-1.5 shadow-sm sm:p-2">
          {tabs.map((t) => (
            <TabsContent key={t.value} value={t.value} className="mt-0 overflow-hidden rounded-lg">
              {t.content}
            </TabsContent>
          ))}
          <BorderBeam size={180} duration={12} colorFrom="#d55e00" colorTo="#0e7c86" />
        </div>
      </Tabs>
    </section>
  );
}

export default Hero195;
