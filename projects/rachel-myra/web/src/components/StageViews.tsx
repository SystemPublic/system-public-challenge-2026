"use client";

import { useState } from "react";
import { STAGE_VIEWS } from "@/lib/journey";

/** Map / graph / patient view switch for a journey stage (decision C5). */
export function StageViews({ panels }: { panels: Record<(typeof STAGE_VIEWS)[number]["id"], React.ReactNode> }) {
  const [view, setView] = useState<(typeof STAGE_VIEWS)[number]["id"]>("map");
  return (
    <div>
      <div role="tablist" aria-label="View" className="flex gap-1 border-b border-line">
        {STAGE_VIEWS.map((v) => (
          <button
            key={v.id}
            role="tab"
            type="button"
            aria-selected={view === v.id}
            onClick={() => setView(v.id)}
            className={`-mb-px rounded-t border px-3 py-1.5 text-sm font-medium ${
              view === v.id ? "border-line border-b-page bg-page" : "border-transparent text-ink-muted"
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" className="pt-4">
        {panels[view]}
      </div>
    </div>
  );
}
