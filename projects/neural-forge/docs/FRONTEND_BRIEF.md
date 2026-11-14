# Front-end brief (read this first)

Build the website for **Ground Truth** in `web/` (this folder's `web/index.html`, `web/app.js`, `web/style.css`).
It reads two files the pipeline already produced and committed. You do NOT need the 1.4 GB data or Python.

```
cd projects/neural-forge
python3 -m http.server 8000 -d web      # open http://localhost:8000
```

Rules: all code written today (hackathon rule); no build step; libraries from CDN, pinned; no API keys anywhere.
Judged 25% on communication: it must look exceptional (dark, calm, precise, cinematic transitions) and explain
itself to a non-specialist in 3 minutes.

## The story the page tells, in order

1. **Whose evidence (opening, full screen).** 767 small dots, one per heat-and-health study in the research graph,
   grouped by region (`evidence_dots[].region`). Counter: "767 studies on heat and health." Then everything dims
   except the NYC dots, which glow: "4 are about New York City." Sub-lines from `headline`: low-income named 5,
   Black or Hispanic named 3, animal studies 66, no place stated 274. A small bar list from `outcomes` shows the same
   pattern for 17 health problems (studies vs NYC studies), e.g. Type 2 diabetes 3,465 vs 3, Depression 878 vs 0.
   Button: "Test the research against New York" → fade to the map.
2. **Map + ledger.** Map of the 59 community districts (`districts.geojson`) on a dark basemap. Layer switch:
   Heat ER burden (`heat_ed_rate`, extruded), **Research needed** (`need_score`, glowing high end; default layer),
   Surface temperature, Street trees, Poverty. Hover: name + value. Click district → panel with its values,
   `need_rank`, `top_need_claim` (link to that claim) and `missing_study`.
   Right panel, always visible: the **ledger**, one card per claim: `title`, verdict chip, ρ and n, "N studies".
   Counts per verdict on top. Verdict colors: confirmed teal, contested coral, bridged violet, inconclusive slate.
3. **Claim detail** (drawer over the ledger):
   - the chain as a small node diagram (`chain[].label`; bridges have 3 nodes; label each link with its
     `research.links[].source`: "research" or "NYC data"; a link with `city_fill` shows its ρ);
   - **Research says**: `research.direction` (+ "more A, more B", − "more A, less B", "mixed" = studies disagree),
     `n_studies`, `n_findings`, a tiny stacked bar of `research.population.regions`, `population.nyc` NYC studies;
   - **New York says**: d3 scatter of `city.scatter` (x, y, name), axis labels `city.x_label` / `city.y_label`,
     `city.rho`, `city.n`, `city.partial_rho_poverty` ("after accounting for poverty"); hovering a dot highlights
     that district on the map only when `city.unit === "community district"` (ids `CD:101`…; UHF42 ids and
     years `Y:2010` have no map shape);
   - for bridges, `city.middle_links` (each with rho, p) and `bridge_note`;
   - verdict, `triage` tags, `resolution` if present, and **"What would settle it"** = `settle` in bold;
   - citations: each of `city.sources` as "collection@semver · ulv3:abcd…" linking to `url`, with `label` and
     `period`; plus `research.graph` the same way and the count of `research.association_ids`.
4. **Version toggle** in the header: "v1.0.0 automated · v1.1.0 hand-checked". Switch compares `verdict_v1` with
   `verdict`; cards whose verdict changed pulse once; link to `meta.claims_collection.compare_url`.
5. **Footer**: `meta.graph_citation`, each `meta.inputs[]` as collection@semver + hash, "Built with Claude Code".

## Data shape (`web/data/ground_truth.json`, 0.2 MB)

```
meta: { title, generated_at, graph_citation, rules[str], excluded_findings,
        inputs[{collection, collection_id, semver, hash, url}],
        claims_collection{owner, slug, url, compare_url, versions[{semver, label}]} }
headline: { studies_total 767, studies_human, studies_nyc 4, studies_mention_new_york 11, studies_us, studies_china,
            studies_europe, studies_no_place, studies_non_human, studies_name_older_adults,
            studies_name_low_income, studies_name_black_or_hispanic, nyc_studies[{study_id, doi, population_string}] }
outcomes[]: { outcome, studies, nyc, us, low_income, black_hispanic, older, no_place }
evidence_dots[]: { study_id, region, human, doi }
   region ∈ NYC | US | China | Europe | East Asia other | Australia | Other place | No place stated | Animal studies
claims[] (11): { id, title, kind: direct|bridge, verdict, verdict_v1, triage[str], settle|null, resolution|null,
   bridge_note|null, note|null,
   chain[{label, concept_ids[], pattern}],
   research{ direction: "+"|"-"|"mixed"|null, n_studies, n_findings, n_excluded_after_review, evidence_fit,
             population{regions{name: count}, nyc, us, older, low_income, black_hispanic, urban},
             links[{from, to, source: graph|city, direction, n_findings, n_studies, city_fill?{rho, p, n, unit,
                    x_label, y_label, sources[]}}],
             dois[], association_ids[], graph{collection, semver, hash, url} },
   city{ x_label, y_label, unit: "community district"|"UHF42 neighborhood"|"year", n, rho, p, q, ci[lo, hi],
         partial_rho_poverty|null, scatter[{id, name, x, y}], middle_links?[{x_label, y_label, n, rho, p}],
         sources[{collection, semver, hash, url, record_type, record_ids[], label, period, query?, measure?}] } }
districts[] (59): { id "CD:101", name, borough, heat_ed_rate|null, heat_hosp_rate|null, surface_temp_f,
   veg_cover_pct, tree_density_per_km2, poverty_pct, older_alone_pct, cold_ed_rate, asthma_ed_rate,
   no_heat_complaints_per_1k, need_score 0–1, need_rank 1–59, top_need_claim, missing_study }
```

`web/data/districts.geojson`: FeatureCollection; `feature.id` = `properties.id` = `CD:101`…, plus `name`, `borough`.

## Libraries (pinned, verified)

```
https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js   (+ /dist/maplibre-gl.css)
https://unpkg.com/deck.gl@9.1.14/dist.min.js               (global `deck`; use deck.MapboxOverlay on the MapLibre map)
https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js
Basemap style (no key): https://tiles.openfreemap.org/styles/dark   center [-73.94, 40.70], zoom ~9.6, pitch 40
Fonts: Google Fonts Inter + JetBrains Mono
```

Build order: map + ledger → claim drawer → opening dots → version toggle → polish. Must look right at 1440×900
on a projector and still work on a laptop. Handle `null` values (two districts have no heat ER rate).

## Paste this into Claude Code to start

> Read `projects/neural-forge/docs/FRONTEND_BRIEF.md` and `projects/neural-forge/web/data/ground_truth.json`.
> Build the site it describes in `projects/neural-forge/web/` (index.html, app.js, style.css), map + ledger first.
> Serve it with `python3 -m http.server 8000 -d web` and check it in the browser after each step.
