# Insights: connections from the concept map

Built on `../mapping/out/concept_map.csv` — see `../mapping/README.md` for the
matching pipeline and `APPROACHES.md` for method choices.

**Read `out/INSIGHTS.md`** — the narrative report with confirmed / bridged /
contested / research-needed classifications, each entry citing the dataset
versions, measure ids, and SPG evidence it rests on.

Outputs:

| file | contents |
|---|---|
| `out/INSIGHTS.md` | the report |
| `out/connections.csv` | 1,132 SPG concept pairs with published associations whose endpoints map to NYC measures (1,047 cross-concept), with association counts, study counts, median effect sizes, and city-side UHF42 Spearman where computable |
| `out/spg_evidence_by_concept_pair.csv` | the association aggregation backing connections.csv |
| `out/bridges.csv` | 921 cross-theme NYC measure pairs that correlate at UHF42 (|ρ|≥0.45) while SPG has no direct association between their mapped concepts; `modeled1/2` flags EHDP burden measures that correlate by construction |
| `out/spot_checks.csv` | 3 flagship direction checks (surface temp × heat ED; grass/tree cover × surface temp; grass/tree cover × heat ED) |
| `out/gaps.json` | unmatched NYC concepts and SPG concepts with no NYC counterpart — the research-needed seed |

Re-run: `python3 -I insights/build_connections.py` (after `mapping/make_outputs.py`).
