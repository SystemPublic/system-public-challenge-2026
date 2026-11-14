# Dashboard build pipeline

The dashboard frontend is the Next.js app in [`../web/`](../web/) — this
directory holds the scripts that produce its data.

## Scripts

- `build_dashboard.py` — stages 0–4 scan the SPG deposit and
  `insights/out` + `mapping/out` (plus a city-ρ matrix over the EHDP bulk
  file and the mixed-chain mediated search); stage 5 writes the JSON bundle
  to `out/bundle.json` and `web/data/bundle.json` (plus
  `out/build_report.json` with assertions). ~6–9 min (two relationship scans).
- `build_districts.py` — downloads the `environment-health` and `geographies`
  collections from Underlay into `../nyc_open_data/data/` (gitignored,
  ~150 MB first run) and writes `web/data/districts.json`: UHF42 boundaries +
  per-measure district values for every bridge measure and every
  confirmation pair's city-check measures (first observation per district —
  the same pivot semantics `insights/build_connections.py` used for the city
  ρ; Spearman parity must pass for all 12 bridge rows and every ρ-bearing
  confirmation pair).

```bash
ln -sfn dashboard/dataverse_files dataverse_files   # deposit expected at repo root
python3 -I dashboard/build_dashboard.py
python3 -I dashboard/build_districts.py
cd web && pnpm install && pnpm dev
```

The old single-file HTML frontend (`src/template.html` + `style.css` +
`app.js`, inlined by `inline.py`) is retired — `out/index.html` is no longer
built. `out/` is derived and gitignored.

## Bundle contents

`meta` (counts + citations), `concepts`/`measures` (label/domain/vintage
lookups), `confirmations` (1,047 cross-concept pairs with evidence + city ρ
+ the inferred SPG direction `dir`/`nsigns` and how the city ρ compares,
`agree`: same / opposite / flat / ambiguous / no_rho — the 26 opposite pairs
are the Contested tab), `egos` (1-hop neighbors per endpoint), `bridges` (the
12 selected bridge rows grouped into 10 concept-set pairs, each with its
connection subgraph: 1-step shared connectors — all edges to both sides,
capped at the strongest 40 — and the strongest 25 two-step corridors,
per-edge findings/studies and association aggregates, plus a ≤250-char
caption), `mediated` (the curated green-space × emergency-care flagship plus
the 30 strongest mixed-evidence chains: one documented SPG hop, one hop
carried entirely by NYC data with no/negligible SPG edge — the assembled
endpoint link does not exist in the graph), and `contested` (cards, spot
checks, vintages, modeled split — the Caveats tab).

Data-quality notes: every concept id is resolved against the authoritative
`concepts-1.csv`; the 12 bridge rows are selected exactly as INSIGHTS.md
selected them (non-modeled candidates, |ρ| descending, stable); both-direction
relationship duplicates are merged keeping the higher-findings record.
Assertions verify 0 direct bridge relationships/associations and byte-stable
counts. Correlations are cross-sectional (42 UHF42 districts), ecological,
unadjusted — directional evidence, not causal replication.
