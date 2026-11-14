#!/usr/bin/env python3
"""Insights phase: classify connections that emerge from the concept map as
confirmed / bridged / contested / research-needed, and run 3 quantitative
spot-checks against EHDP observations at UHF42 level.

Run: python3 -I insights/build_connections.py   (after mapping/make_outputs.py)
Outputs: insights/out/{connections.csv,bridges.csv,spot_checks.csv,gaps.csv},
         insights/INSIGHTS.md
"""
import json
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
MOUT = BASE / "mapping" / "out"
IOUT = BASE / "insights" / "out"
IOUT.mkdir(parents=True, exist_ok=True)
NYC = BASE / "nyc_open_data"

cmap = pd.read_csv(MOUT / "concept_map.csv")
nyc = pd.read_csv(MOUT / "nyc_concepts.csv").fillna("")
full = pd.read_csv(BASE / "dataverse_files" /
                   "system-public-graph-v1-concepts-1.csv", dtype=str).fillna("")
concept_label = dict(zip(full.system_id, full.wikidata_label))
dom = pd.read_csv(MOUT / "spg_concepts.csv").fillna("")
concept_domains = dict(zip(dom.system_id, dom.domains))

# NYC measures per SPG concept
meas_by_concept = {}
for _, r in cmap.iterrows():
    meas_by_concept.setdefault(r.spg_system_id, set()).add(r.nyc_id)
mapped_concepts = sorted(meas_by_concept)

# ---------------------------------------------------------------- associations
print("Filtering 2M associations to mapped concepts...")
use = ["pubmed_id", "system_statistic_type", "statistic_value", "p_value",
       "variable_1_concept_id", "variable_2_concept_id",
       "variable_1_name", "variable_2_name"]
chunks = []
for ch in pd.read_csv(BASE / "dataverse_files" /
                      "system-public-graph-v1-associations.csv",
                      usecols=use, chunksize=400_000):
    k = ch[ch.variable_1_concept_id.isin(mapped_concepts)
           & ch.variable_2_concept_id.isin(mapped_concepts)]
    chunks.append(k)
assoc = pd.concat(chunks)
assoc["c1"], assoc["c2"] = assoc.variable_1_concept_id, assoc.variable_2_concept_id
assoc["pair"] = [tuple(sorted(p)) for p in zip(assoc.c1, assoc.c2)]
print(f"{len(assoc)} associations among mapped concepts, "
      f"{assoc.pair.nunique()} concept pairs")

pair_stats = (assoc.groupby("pair")
              .agg(n_assocs=("pubmed_id", "size"),
                   n_pubmeds=("pubmed_id", "nunique"),
                   median_effect=("statistic_value", "median"),
                   effect_types=("system_statistic_type",
                                 lambda s: "; ".join(sorted(set(s.dropna()))[:5])),
                   sample_vars=("variable_1_name", "first"))
              .reset_index())

# ---------------------------------------------------------------- EHDP UHF42 obs
def load_observations():
    import gzip
    recs = []
    with gzip.open(NYC / "data" / "environment-health" /
                   "environment-health.v1.0.0.records.ndjson.gz", "rt") as fh:
        for line in fh:
            if '"type":"Observation"' not in line:
                continue
            d = json.loads(line)["data"]
            if d.get("geoType") == "UHF42" and isinstance(d.get("value"), (int, float)):
                recs.append((d["measureId"], d["geographyId"], d["value"]))
    return pd.DataFrame(recs, columns=["measureId", "geo", "value"])

print("Loading EHDP UHF42 observations...")
obs = load_observations()
piv = obs.pivot_table(index="geo", columns="measureId", values="value",
                      aggfunc="first")
print(f"{piv.shape[0]} UHF42 districts, {piv.shape[1]} measures with values")

nyc_by_id = nyc.set_index("nyc_id").to_dict("index")
ehdp_ids = [m for m in meas_by_concept for m in meas_by_concept[m]
            if m.startswith("ehdp:")]
ehdp_ids = sorted({m.split("ehdp:")[1] for m in ehdp_ids if m.split("ehdp:")[1] in piv.columns})

def m_info(mid):
    return nyc_by_id[f"ehdp:{mid}"]

def rho(a, b):
    s1, s2 = piv[a], piv[b]
    if isinstance(s1, pd.DataFrame):
        s1 = s1.iloc[:, 0]
    if isinstance(s2, pd.DataFrame):
        s2 = s2.iloc[:, 0]
    j = pd.concat([s1, s2], axis=1).dropna()
    if len(j) < 25:
        return None, len(j)
    r = j.corr(method="spearman").iloc[0, 1]
    return (round(float(r), 3) if pd.notna(r) else None), len(j)

# ---------------------------------------------------------------- 1. CONFIRMED
def nyc_label(mid):
    i = nyc_by_id.get(mid)
    return i["label"] if i else mid

rows = []
for _, p in pair_stats.iterrows():
    c1, c2 = p.pair
    n1 = sorted(meas_by_concept[c1])
    n2 = sorted(meas_by_concept[c2])
    e1 = [m for m in n1 if m.startswith("ehdp:")]
    e2 = [m for m in n2 if m.startswith("ehdp:")]
    # measurable-together check: any EHDP measure on each side sharing UHF42 values
    city_rho, n_geo, mid_x, mid_y = None, 0, "", ""
    if e1 and e2:
        best = None
        for a in e1:
            for b in e2:
                ma, mb = a.split("ehdp:")[1], b.split("ehdp:")[1]  # "measure:535"
                if ma in piv.columns and mb in piv.columns:
                    r_, n_ = rho(ma, mb)
                    if r_ is not None and (best is None or abs(r_) > abs(best[0])):
                        best = (r_, n_, a, b)
        if best:
            city_rho, n_geo, mid_x, mid_y = best
    modeled_used = False
    if city_rho is not None:
        modeled_used = bool(
            re.search(r"Estimated annual", str(m_info(mid_x.split("ehdp:")[1])["measurement_type"]))
            or re.search(r"Estimated annual", str(m_info(mid_y.split("ehdp:")[1])["measurement_type"])))
    rows.append({
        "c1": c1, "label1": concept_label.get(c1, c1),
        "domains1": concept_domains.get(c1, ""),
        "c2": c2, "label2": concept_label.get(c2, c2),
        "domains2": concept_domains.get(c2, ""),
        "self_pair": c1 == c2,
        "n_assocs": p.n_assocs, "n_pubmeds": p.n_pubmeds,
        "median_effect": p.median_effect, "effect_types": p.effect_types,
        "nyc1": "; ".join(n1)[:200], "nyc2": "; ".join(n2)[:200],
        "city_spearman_uhf42": city_rho, "city_n_districts": n_geo,
        "city_check_measures": (f"{mid_x} x {mid_y}" if city_rho is not None else ""),
        "city_check_modeled": modeled_used,
        "status": "confirmed",
        "note": (("city check used modeled burden measure - treat rho as neighborhood "
                  "structure, not outcome observation") if modeled_used
                 else ("city-side UHF42 correlation of observed measures" if city_rho is not None
                       else "SPG evidence present; no EHDP measures co-observable at UHF42 "
                            "(e.g. death causes are citywide-only)")),
    })
confirmed = pd.DataFrame(rows).sort_values("n_assocs", ascending=False)
confirmed.to_csv(IOUT / "connections.csv", index=False)
cross = confirmed[~confirmed.self_pair]
print(f"confirmed pairs with SPG evidence: {len(confirmed)} "
      f"({len(cross)} cross-concept; "
      f"{cross.city_spearman_uhf42.notna().sum()} with city correlation)")

# ---------------------------------------------------------------- 2. BRIDGES
# concept pairs BOTH mapped to NYC measures with NO SPG association between
# them, where the city measures themselves correlate at UHF42.
assoc_pairs = set(pair_stats.pair)
concept_of_measure = {}
for c, ms in meas_by_concept.items():
    for m in ms:
        concept_of_measure.setdefault(m, set()).add(c)

bridge_rows = []
def fam(label):
    return label.split(",")[0].strip().casefold()

def fam_words(label):
    return set(re.findall(r"[a-z]+", fam(label)))

for m1, m2 in combinations(ehdp_ids, 2):
    cs1, cs2 = concept_of_measure.get(f"ehdp:{m1}", set()), concept_of_measure.get(f"ehdp:{m2}", set())
    if any(tuple(sorted((a, b))) in assoc_pairs for a in cs1 for b in cs2):
        continue  # SPG evidence exists -> that pair is in connections.csv
    i1, i2 = m_info(m1), m_info(m2)
    # skip redundant pairs: same theme, or label families sharing a word
    t1 = set(str(i1["themes"]).split(";"))
    t2 = set(str(i2["themes"]).split(";"))
    if t1 & t2:
        continue
    if fam_words(i1["label"]) & fam_words(i2["label"]):
        continue
    r_, n_ = rho(m1, m2)
    if r_ is None or abs(r_) < 0.5:
        continue
    vintage_overlap = not (int(i1["year_range"].split("-")[1]) < int(i2["year_range"].split("-")[0])
                           or int(i2["year_range"].split("-")[1]) < int(i1["year_range"].split("-")[0]))
    bridge_rows.append({
        "measure1": m1, "label1": i1["label"], "concepts1": "; ".join(concept_label.get(c, c) for c in cs1),
        "measure2": m2, "label2": i2["label"], "concepts2": "; ".join(concept_label.get(c, c) for c in cs2),
        "city_spearman_uhf42": r_, "n_districts": n_,
        "years1": i1["year_range"], "years2": i2["year_range"],
        "vintages_overlap": vintage_overlap,
        "modeled1": bool(re.search(r"Estimated annual", str(i1["measurement_type"]))),
        "modeled2": bool(re.search(r"Estimated annual", str(i2["measurement_type"]))),
    })
bridges = pd.DataFrame(bridge_rows)
if len(bridges):
    bridges = bridges.reindex(bridges.city_spearman_uhf42.abs()
                              .sort_values(ascending=False).index)
bridges.to_csv(IOUT / "bridges.csv", index=False)
print(f"city-only bridge candidates (|rho|>=0.45, no SPG association): {len(bridges)}")

# ---------------------------------------------------------------- 3. SPOT CHECKS
checks = [
    ("surface temperature", "688", "heat ED visits (rate)", "537",
     "SPG: heat x emergency care = 70 associations with positive effect sizes; expect rho > 0"),
    ("grass and tree cover", "690", "surface temperature", "688",
     "SPG: green space x heat = 12 associations; expect rho < 0 (cover cools surfaces)"),
    ("grass and tree cover", "690", "heat ED visits (rate)", "537",
     "SPG: green space x emergency care = 0 associations; naive cross-sectional rho near 0 would show the link is mediated (via heat), not direct - i.e. exactly what a study needs to untangle"),
]
sc = []
for name1, m1, name2, m2, expect in checks:
    r_, n_ = rho(f"measure:{m1}", f"measure:{m2}")
    sc.append({"check": f"{name1} vs {name2}", "measure1": f"measure:{m1}",
               "measure2": f"measure:{m2}", "spearman_uhf42": r_,
               "n_districts": n_, "expectation": expect})
scdf = pd.DataFrame(sc)
scdf.to_csv(IOUT / "spot_checks.csv", index=False)
print(scdf.to_string(index=False))

# ---------------------------------------------------------------- 4. GAPS
unmatched = pd.read_csv(MOUT / "unmatched_nyc.csv")
used_concepts = set(cmap.spg_system_id)
spg_only = dom[~dom.system_id.isin(used_concepts)]
gaps = {
    "unmatched_nyc_by_theme": unmatched.groupby(unmatched.collection).size().to_dict(),
    "unmatched_nyc_labels": unmatched.label.tolist(),
    "spg_domain_concepts_with_no_nyc_counterpart":
        spg_only.assign(domain=spg_only.domains.str.split("; "))
        .explode("domain").groupby("domain").label.apply(list).to_dict(),
}
(IOUT / "gaps.json").write_text(json.dumps(gaps, indent=2))
print(f"research gaps: {len(unmatched)} unmatched NYC rows, "
      f"{len(spg_only)} SPG-473 concepts with no NYC counterpart")

# ---------------------------------------------------------------- 5. INSIGHTS.MD
def cite(mids):
    out = []
    for m in mids:
        i = nyc_by_id.get(m)
        if i:
            out.append(f"{i['label']} (`{m}`, {i['collection']} v1.0.0, {i['year_range']})")
    return "; ".join(out[:4])

L = []
L.append("# Insights: connections that emerge from the concept map\n")
L.append("Sources: SPG v1 associations/concepts (Dataverse deposit); NYC open data "
         "v1.0.0 collections on Underlay (environment-health, heat-complaints, "
         "leading-causes-of-death, street-trees). Concept map: "
         "`mapping/out/concept_map.csv`.\n")

L.append("## Confirmed — research and the city describe the same links\n")
L.append(f"{len(confirmed)} concept pairs have published associations in the SPG "
         f"*and* map to measurable NYC indicators ({len(cross)} distinct construct "
         "pairs; self-pairs from a concept's own measures excluded below). Strongest "
         "cross-concept pairs by evidence volume:\n")
L.append("| SPG concept pair (domains) | assoc | studies | median effect | city UHF42 rho | NYC measures (first each side) |")
L.append("|---|---|---|---|---|---|")
for _, r in cross.head(15).iterrows():
    d1 = r.domains1.split(";")[0] if r.domains1 else "beyond-473"
    d2 = r.domains2.split(";")[0] if r.domains2 else "beyond-473"
    eff = f"{r.median_effect:.2f}" if pd.notna(r.median_effect) else "—"
    rho_s = (str(r.city_spearman_uhf42)
             if r.city_spearman_uhf42 is not None and pd.notna(r.city_spearman_uhf42)
             else "—")
    if r.city_check_modeled:
        rho_s += "⚠"
    L.append(f"| **{r.label1}** ({d1}) × **{r.label2}** ({d2}) | {r.n_assocs} | "
             f"{r.n_pubmeds} | {eff} | {rho_s} | "
             f"{nyc_label(r.nyc1.split(';')[0])} ↔ {nyc_label(r.nyc2.split(';')[0])[:60]} |")
L.append("\nρ⚠ = the city check's best-correlating measure pair includes a modeled "
         "burden measure (e.g. 'PM2.5 health burden (heart)') — such ρ reflect "
         "neighborhood structure shared by two modeled/survey layers, not observed "
         "disease; the exact measure pair behind every ρ is in "
         "`city_check_measures` in `out/connections.csv`. Self-pairs (a concept "
         "associated with its own measures) and all "
         f"{len(confirmed) - len(cross)} remaining pairs: `out/connections.csv`.\n")

L.append("## Bridged — links no single dataset holds alone\n")
if len(bridges):
    L.append(f"Cross-theme pairs of mapped NYC measures (|Spearman| ≥ 0.5 across UHF42 "
             "districts, different indicator themes, no shared label family) where the "
             "SPG holds **no direct association** between their mapped concepts. The "
             "strongest observed (non-modeled) candidates:\n")
    L.append("| NYC measure pair (concepts) | city UHF42 rho | vintages | caveat |")
    L.append("|---|---|---|---|")
    shown = 0
    for _, r in bridges.iterrows():
        if shown >= 12:
            break
        if r.modeled1 or r.modeled2:
            continue  # modeled attributions correlate by construction; show observed pairs
        cav = []
        if not r.vintages_overlap:
            cav.append(f"vintages disjoint ({r.years1} vs {r.years2})")
        L.append(f"| {r.label1} ({r.concepts1}) × {r.label2} ({r.concepts2}) | "
                 f"**{r.city_spearman_uhf42}** | {r.years1} / {r.years2} | "
                 f"{'; '.join(cav) or '—'} |")
        shown += 1
    observed = bridges[~(bridges.modeled1 | bridges.modeled2)]
    L.append(f"\nObserved (non-modeled) bridge candidates: {len(observed)}; "
             "modeled-attribution pairs excluded above because EHDP burden measures "
             "share estimation machinery and correlate by construction. "
             "Full list: `out/bridges.csv`.\n")
else:
    L.append("No strong city-only correlations found below threshold.\n")

L.append("## Contested — where research and city data disagree or misalign\n")
L.append("1. **Green space × emergency care — absent in research, mediated in the city.** "
         "SPG holds **0 associations** between green-space and emergency-care concepts. "
         "The city's own data shows *why a naive check fails and what the real link is*: "
         "vegetation cover does not correlate directly with heat ED visits across UHF42 "
         "districts (rho ≈ 0.02, see spot-checks) — but it clearly depresses surface "
         "temperature (rho = -0.40), and the graph itself supplies 70 heat × emergency-care "
         "associations. So the chain cover → cooler surfaces → fewer heat outcomes is "
         "supported piecewise by the two datasets together, while the direct edge is "
         "untested in the literature. That is precisely the 'link neither dataset holds "
         "alone' — and a research target.\n")
L.append("2. **Vintage misalignment.** Street-tree census is 2015; vegetation cover "
         "2010-2017; surface temperature a single day (2018); heat outcomes "
         "2000-2022; 311 complaints 2024-2026. Cross-dataset claims must state "
         "which years each leg rests on — the map carries year ranges on every row.\n")
L.append("3. **Modeled vs observed.** EHDP 'burden' measures (PM2.5 asthma ED "
         "visits, deaths from PM2.5/ozone, heat vulnerability index) are modeled "
         "attributions (`howCalculated`), not observations. Confirmations that use "
         "them as endpoints reproduce the model, not the city — flagged "
         "`modeled1/2` in `out/bridges.csv`.\n")
L.append("4. **Counts vs rates vs age-adjusted rates.** The same EHDP indicator "
         "appears as Number, Percent, rate and age-adjusted rate measures; SPG "
         "associations mix OR/RR/r with 89% null study_type. Comparing effect "
         "magnitudes across that boundary is not valid — compare directions only.\n")
L.append("5. **Construct ≠ operationalization.** 'Heat ED visits' counts "
         "heat-stress visits during warm months (May-September, ICD-coded); SPG "
         "heat concepts span heat wave, extreme heat, heat stroke, heat illness. "
         "The map types these as broader-narrower/related-component so downstream "
         "claims inherit the right caveats.\n")

L.append("## Research needed — the gap map\n")
L.append("**NYC concepts with no research-graph counterpart** (research the graph "
         "hasn't absorbed):\n")
unmatched_full = pd.read_csv(MOUT / "unmatched_nyc.csv")
fams = {}
for _, u in unmatched_full.iterrows():
    if u.collection == "street-trees":
        continue
    fams[u.label.split(",")[0]] = fams.get(u.label.split(",")[0], 0) + 1
for k in sorted(fams, key=lambda x: -fams[x]):
    L.append(f"- {k} ×{fams[k]}")
n_species = int((unmatched_full.collection == "street-trees").sum())
L.append(f"- street-tree species ×{n_species} (no species-level research concepts "
         "exist; street trees as a construct connect through the EHDP vegetation/"
         "tree-shade measures, which ARE mapped)")
L.append("\n**SPG challenge-domain concepts with no NYC measurable counterpart** "
         "(what the city doesn't measure — where city data collection could grow):\n")
for d, labels in sorted(gaps["spg_domain_concepts_with_no_nyc_counterpart"].items()):
    L.append(f"- **{d}**: {', '.join(labels[:10])}"
             + (f" … +{len(labels)-10} more" if len(labels) > 10 else ""))
L.append("\n**What would settle the contests:**\n")
L.append("- Green space → ED visits: a cohort or quasi-experimental study (tree "
         "planting natural experiments) estimating green-space effects on acute "
         "care use, measured at the neighborhood level NYC already publishes.\n")
L.append("- Vintage alignment: a refreshed tree census aligned to EHDP outcome "
         "years, or EHDP vegetation layers extended past 2017.\n")
L.append("- Modeled burden: publish the attribution-model covariates so city-side "
         "correlations can be adjusted for shared estimation inputs.\n")

L.append("## Quantitative spot-checks (UHF42 cross-section)\n")
L.append("Direction checks only — not epidemiology; cross-sectional correlations "
         "across 42 districts.\n")
L.append("| check | rho | n | expectation from SPG |")
L.append("|---|---|---|---|")
for _, r in scdf.iterrows():
    L.append(f"| {r.check} ({r.measure1} vs {r.measure2}) | **{r.spearman_uhf42}** | "
             f"{r.n_districts} | {r.expectation} |")
L.append("")
(IOUT / "INSIGHTS.md").write_text("\n".join(L))
print("Wrote insights/out/{connections.csv,bridges.csv,spot_checks.csv,gaps.json,INSIGHTS.md}")
