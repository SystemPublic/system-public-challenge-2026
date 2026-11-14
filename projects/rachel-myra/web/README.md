# web/ — The Missing Label app

Next.js 16 (App Router, Turbopack, Cache Components) + TypeScript + Tailwind v4, light mode only.
Clinician tool, public story and the patient app "My Medicine Cabinet" in one codebase (spec §4.8).

> **Note for AI agents:** this is Next.js **16.4**. APIs differ from older versions (see `AGENTS.md`).
> Read `node_modules/next/dist/docs/` before changing config, caching or routing.

## Run

```bash
cd web
npm install          # uses ~/.npm cache; already done on the build machine
npm run dev          # http://localhost:3000
npm run build        # production build (verified passing)
npm run lint         # eslint (verified passing)
```

Pages read the knowledge base at render time. In `dev` they re-read it on each request; after the
KB changes, a production build needs `npm run build` again (pages are prerendered).

## Structure

```
web/
  next.config.ts            turbopack.root + outputFileTracingRoot = repo root (so ../lib and ../data resolve)
  tsconfig.json             aliases: @/* → src/*, @lib/* → ../lib/*, @kb/* → ../data/kb/*, @processed/* → ../data/processed/*
                            allowImportingTsExtensions: lib/ uses "./x.ts" imports
  src/styles/tokens.css     design tokens (spec §3.3); contrast notes inline
  src/app/globals.css       Tailwind v4 @theme extension exposing the tokens as utilities
  src/lib/kb.ts             data-access layer (server only, node:fs)
  src/lib/ui.ts             bucket / meter / badge / layer / compass display metadata (client-safe)
  src/lib/journey.ts        the 6 journey stages (spec §6.9)
  src/components/           badges.tsx (Dash, BucketChip, EvidenceMeter, LevelMeter, VerificationBadge,
                            LayerTag, CompassArrowMark, GapBadge), PeriodicTable (client), BucketEvidenceChart
                            (ECharts, client), SiteHeader, Disclaimer, KbSourceBanner, Placeholder, StageViews
  src/app/
    page.tsx                /            public story (placeholder) + journey cards
    map/                    /map         Evidence Map: periodic table, filters, legend
    drug/[id]/              /drug/:id    Drug Card (prerendered for every KB drug)
    readiness/              /readiness   Heat-Wave Readiness (placeholders + lib/thermal place list)
    evidence/               /evidence    nerd stats: KB info, bucket×evidence chart, badge counts, guidance kappa
    patient/                /patient     My Medicine Cabinet (large type, demo cabinet)
    journey/[stage]/        /journey/:stage  one page per stage with Map / Graph / Patient view tabs
    api/cds-hooks/          GET discovery (stub); POST /api/cds-hooks/heat-medication-check → {cards: []}
    api/system-live/        GET stub, no external calls
    api/kb/                 GET which KB file is loaded + drug ids
```

Every page shows the disclaimer **"Prototype. Considerations for clinicians, not instructions."**
(black strip in the header and in the footer).

## Knowledge base loading (`src/lib/kb.ts`)

1. `../data/kb/knowledge_base.json` (real, from the pipeline)
2. `../data/kb/mock_knowledge_base.json` (mock, same shape)
3. inline one-drug fallback (lithium; wording from spec only, no numbers, no claims)

Typed against `lib/types/knowledge-base.ts` (`KnowledgeBase`, `DrugRecord`). A yellow banner
(`KbSourceBanner`) appears whenever the mock or fallback is in use. Claims are filtered with
`isPublicClaim()` so "?" (unverified) claims never reach labels. Missing values render as "—"
(`<Dash/>`); the UI never invents numbers.

Other helpers: `readProcessedJson(name)` and `listProcessedFiles()` for `../data/processed/`.

## Design tokens and contrast (WCAG 2.1 AA)

Light mode only. Bucket hues are Okabe–Ito (colorblind-safe) and always paired with a letter
(A / H / M / S) and a text label. Ratios computed with the WCAG relative-luminance formula.

| Token | Use | Pair | Ratio |
|---|---|---|---|
| Adjust dose `#e69f00` | solid fill (Strong) | text `#141414` | 8.18 |
| Hold / substitute `#d55e00` | solid fill | text `#141414` | 4.76 |
| Monitor `#cc79a7` | solid fill | text `#141414` | 6.02 |
| Store cool `#0072b2` | solid fill | text `#ffffff` | 5.19 |
| Adjust ink `#8a5a00` | text/outline (Early signs) | on white / on tint `#fcf0d6` | 5.93 / 5.24 |
| Hold ink `#a0410a` | " | white / tint `#fbe3d6` | 6.45 / 5.24 |
| Monitor ink `#9c3d74` | " | white / tint `#f6e4ee` | 6.30 / 5.18 |
| Store ink `#005a8c` | " | white / tint `#dcebf5` | 7.39 / 6.07 |
| Ink `#141414` / muted `#4b5563` | body text | white | 18.4 / 7.56 |
| Strong line `#6b6b66` | meter segment borders (graphic, needs 3:1) | white | 5.36 |
| ✓✓ `#065f46` on `#d1fae5`, ✓ on `#ecfdf5` | verification | | 6.78 / 7.29 |
| ↗ `#1e40af` on `#dbeafe` | corroborated | | 7.15 |
| ⚠ `#92400e` on `#fef3c7` | conflict | | 6.37 |
| ? `#374151` on `#e5e7eb` | unverified | | 8.33 |
| ① graph `#3730a3`/`#eef2ff`, ② lit `#166534`/`#f0fdf4`, ③ FDA `#9a3412`/`#fff7ed` | layer tags | | 8.88 / 6.81 / 6.88 |
| Compass ↑ `#a0410a`, ↓ `#005a8c`, ↕ `#4b5563` | arrows | white | 6.45 / 7.39 / 7.56 |

Not AA as text (used only as fills, never as text on white): the raw bucket solids against white
(e.g. `#e69f00` is 2.25:1), which is why outlines and text use the darker "ink" variants.

Evidence fill: **solid = Strong, pale tint = Some, outline = Early signs**. Guidance gap = dashed
black ring + "!" badge. Patient scale: `text-patient-base` 20px, `-lg` 24, `-xl` 30, `-2xl` 38;
`min-h-tap` = 56px tap targets.

Tailwind utilities: `bg-adjust-solid`, `text-hold-ink`, `bg-store-tint`, `bg-verify-double-bg`,
`text-layer-graph-fg`, `text-compass-up`, `text-patient-xl`, `min-h-tap`, `rounded-tile`, etc.

## What's stubbed

- Public story narrative, evidence-vs-guidance quadrant, Sankeys, node graph, forest plot,
  call-first scatter, simulator, playbook, 3D map, patient check-ins: labelled `Placeholder` boxes.
- CDS Hooks returns no cards yet; `/api/system-live` makes no external calls.
- Patient cabinet shows the first 6 KB drugs as an example until the synthetic panel
  (`lib/patient`, `lib/types/patient.ts`) is wired in.
- No Supabase, no SMS, no push yet (spec: SMS is simulated in the demo).

## Install later (skipped: disk had ~1 GB free after the core install)

```bash
cd web
npm install deck.gl maplibre-gl react-force-graph-2d   # 3D NYC map + node graph
npm install @supabase/supabase-js                      # optional, cross-device live updates
```

`react-force-graph-2d` (rather than the full `react-force-graph`, which pulls in three.js/VR deps)
is enough for the required 2D node graph. Use `next/dynamic` with `ssr: false` for deck.gl,
MapLibre and force-graph components (they touch `window`).
