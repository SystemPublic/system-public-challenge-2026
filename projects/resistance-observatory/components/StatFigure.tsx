"use client";

import { useEffect, useState } from "react";
import type { Stat } from "@/lib/stats";
import { useInView, usePrefersReducedMotion } from "@/lib/motion";

/**
 * Renders a Stat from lib/stats.ts. Numeric values count up on first scroll
 * into view (static under reduced motion). Text values render as they are.
 */
export function StatFigure({
  stat,
  className = "",
  showLabel = true,
  showSource = true,
  size = "lg",
}: {
  stat: Stat;
  className?: string;
  showLabel?: boolean;
  showSource?: boolean;
  size?: "lg" | "md";
}) {
  const { ref, inView } = useInView<HTMLDivElement>({ threshold: 0.4 });
  const reduced = usePrefersReducedMotion();
  const target = typeof stat.value === "number" ? stat.value : null;
  const [shown, setShown] = useState<number | null>(target === null ? null : 0);

  useEffect(() => {
    if (target === null) return;
    if (reduced) {
      setShown(target);
      return;
    }
    if (!inView) return;
    let raf = 0;
    const start = performance.now();
    const dur = 1600;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(target * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, reduced, target]);

  const decimals = target !== null && !Number.isInteger(target) ? 1 : 0;
  const sizeClass = size === "lg" ? "text-6xl sm:text-7xl" : "text-4xl sm:text-5xl";

  return (
    <div ref={ref} className={className}>
      <p className={`font-display ${sizeClass} font-semibold tracking-tight tabular-nums leading-none`}>
        {target !== null ? (
          <>
            {/* Screen readers get the final figure, not the animation. */}
            <span aria-hidden>
              {(shown ?? 0).toLocaleString("en-US", {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
              })}
              {stat.unit ?? ""}
            </span>
            <span className="sr-only">
              {target.toLocaleString("en-US")}
              {stat.unit ?? ""}
            </span>
          </>
        ) : (
          <>
            {String(stat.value)}
            {stat.unit ?? ""}
          </>
        )}
      </p>
      {showLabel ? <p className="mt-3 max-w-xs text-sm text-muted">{stat.label}</p> : null}
      {showSource ? <p className="mt-1 font-mono text-[0.7rem] text-muted">Source: {stat.source}</p> : null}
    </div>
  );
}
