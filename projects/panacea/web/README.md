# SPG × NYC — dashboard web app

The dashboard as a Next.js app (App Router, fully static), typeset after
[Tufte CSS](https://edwardtufte.github.io/tufte-css/) — cream paper, hairline
rules, EB Garamond, small-caps labels.

## Routes

| Route | Contents |
| --- | --- |
| `/` | **Confirmations** — cross-concept pairs with published associations whose endpoints map to NYC measures and whose city correlation agrees with (or doesn't contradict) the published effects. Searchable/sortable table with the inferred SPG direction; click a row for the pair's district correlation maps, 1-hop research-graph ego view, evidence, and the same/opposite verdict. ρ⚠ marks checks that used a modeled burden measure. |
| `/contested` | **Contested** — the pairs whose district-level city correlation points opposite to the direction the published effects imply. Same table, same row popup. |
| `/bridges` | **Bridges** — search an overall theme, pick a candidate pair, and see every research-graph connection between the two concept sets as a deterministic layered graph (no force layout, so it never wobbles), plus side-by-side UHF42 choropleths of both measures — the same district values the ρ summarizes. |
| `/mediated` | **Mediated** — mixed-evidence chains: one documented SPG hop plus one hop carried entirely by NYC data, assembling endpoint connections that exist in neither dataset alone. Curated green-space → emergency-care flagship first. |
| `/caveats` | **Caveats** — the five caveats the concept map forces on every claim, the flagship direction spot-checks, the modeled-vs-observed split, and the measurement-vintage timeline. |

## Data

`data/bundle.json` and `data/districts.json` are committed so the app builds
and deploys standalone. Both are derived:

- `bundle.json` — written by `../dashboard/build_dashboard.py` (needs the SPG
  Dataverse deposit; see `../dashboard/README.md`). Types in `src/lib/bundle.ts`.
- `districts.json` — written by `../dashboard/build_districts.py` (downloads
  the `environment-health` and `geographies` collections from Underlay into
  `../nyc_open_data/data/`, gitignored). Exports, per measure, the first-seen
  UHF42 observation per district — the exact
  `pivot_table(aggfunc="first")` semantics the city ρ was computed with,
  plus UHF42 boundaries (polygons → rings → `[lon, lat]`).

To refresh either: run the script, it writes straight into `data/`.

## Develop

```sh
pnpm install
pnpm dev      # http://localhost:3000
pnpm build    # static output, must pass before shipping
pnpm lint
```
