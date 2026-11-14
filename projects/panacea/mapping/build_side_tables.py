#!/usr/bin/env python3
"""Build normalized side tables for SPG <-> NYC concept matching.

SPG side:  the 473 domain-tagged challenge concepts (from eda/out/domain_concepts.csv)
           enriched with aliases/descriptions from the full concepts CSV.
NYC side:  every concept-bearing surface of the 7 Underlay collections:
           EHDP challenge measures, leading causes of death (w/ ICD-10),
           heat-complaint conditions, street-tree species.
Outputs to mapping/out/{spg_concepts.csv,nyc_concepts.csv} + a build summary.
Run: python3 -I mapping/build_side_tables.py   (from repo root or anywhere; paths from __file__)
"""
import gzip
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent  # repo root
OUT = BASE / "mapping" / "out"
OUT.mkdir(parents=True, exist_ok=True)
NYC = BASE / "nyc_open_data"
DV = BASE / "dataverse_files"

# ---------------------------------------------------------------- helpers
def collection_version(slug: str) -> str:
    meta = json.loads((NYC / "out" / "meta" / f"{slug}.version.json").read_text())
    h = (meta.get("hash") or "").replace("ulv3:", "")
    return f"{meta.get('semver', '?')} (ulv3:{h[:12]}…)"


def iter_records(slug: str):
    path = NYC / "data" / slug / f"{slug}.v1.0.0.records.ndjson.gz"
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if '"type":"' not in line:
                continue
            yield json.loads(line)


def trim(s, n=220):
    if not isinstance(s, str):
        return ""
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n] + ("…" if len(s) > n else "")


# ---------------------------------------------------------------- SPG side
domains = pd.read_csv(BASE / "eda" / "out" / "domain_concepts.csv")
dom_map = domains.groupby("system_id")["domain"].apply(lambda s: "; ".join(sorted(set(s))))

concepts = pd.read_csv(DV / "system-public-graph-v1-concepts-1.csv",
                       dtype=str).fillna("")
spg = concepts[concepts["system_id"].isin(dom_map.index)].copy()
spg["domains"] = spg["system_id"].map(dom_map)
spg["aliases"] = spg["wikidata_aliases"].apply(
    lambda s: "; ".join(json.loads(s)) if s.startswith("[") else s)
spg_out = spg[["system_id", "wikidata_id", "wikidata_label", "aliases",
               "wikidata_description", "domains"]].rename(columns={
    "wikidata_label": "label", "wikidata_description": "description"})
spg_out.to_csv(OUT / "spg_concepts.csv", index=False)
print(f"SPG side: {len(spg_out)} concepts, "
      f"{spg_out['domains'].str.contains('&').sum()} rows tagged multi-domain")

# ---------------------------------------------------------------- NYC side
rows = []
vers = {s: collection_version(s) for s in
        ["environment-health", "leading-causes-of-death", "heat-complaints",
         "street-trees", "geographies"]}

# 1. EHDP challenge measures
cat = pd.read_csv(NYC / "out" / "tables" / "ehdp_challenge_indicators.csv")
for _, r in cat.iterrows():
    rows.append({
        "nyc_id": f"ehdp:{r['measureId']}",
        "collection": "environment-health",
        "version": vers["environment-health"],
        "record_type": "Measure",
        "label": r["measure"],
        "description": trim(r["description"]),
        "measurement_type": r["measurementType"],
        "how_calculated": trim(r["howCalculated"]),
        "indicator_name": r["indicator"],
        "icd10": "",
        "geo_types": r["geoTypes"],
        "year_range": f"{r['year_min']:.0f}-{r['year_max']:.0f}",
        "observations": int(r["observations"]),
        "themes": r["themes"],
    })
print(f"EHDP challenge measures: {len(cat)}")

# 2. Leading causes of death — canonicalize by cause label (code sets vary by year)
def norm_cause(name: str) -> str:
    n = re.sub(r"\s+", " ", name.strip())
    n = (n.replace("Posioning", "Poisoning")      # DOHMH typo, some years
          .replace("Nephrisis", "Nephrosis")      # DOHMH typo
          .replace("Chronic Liver Diseases", "Chronic Liver Disease"))
    return n


cause_codes: dict[str, Counter] = {}
cause_labels: dict[str, Counter] = {}
cause_years: dict[str, set] = {}
for rec in iter_records("leading-causes-of-death"):
    if rec["type"] != "CauseOfDeath":
        continue
    d = rec["data"]
    code = d.get("icd10Codes", "")
    if not code or code == "All Other Causes":
        continue
    label = norm_cause(d["causeName"])
    key = label.casefold()
    cause_codes.setdefault(key, Counter())[code] += 1
    cause_labels.setdefault(key, Counter())[label] += 1
    cause_years.setdefault(key, set()).add(d.get("year"))
for key, codes in sorted(cause_codes.items()):
    label = cause_labels[key].most_common(1)[0][0]
    code_sets = "; ".join(sorted(codes))
    variants = "; ".join(sorted(set(codes) - {codes.most_common(1)[0][0]}))
    desc = f"ICD-10: {code_sets}"
    if variants:
        desc += f" (definition varies by year: {variants})"
    rows.append({
        "nyc_id": f"deaths:{key}",
        "collection": "leading-causes-of-death",
        "version": vers["leading-causes-of-death"],
        "record_type": "CauseOfDeath",
        "label": label,
        "description": desc,
        "measurement_type": "deaths; deathRate; ageAdjustedDeathRate",
        "how_calculated": "",
        "indicator_name": label,
        "icd10": code_sets,
        "geo_types": "Citywide (by sex, raceEthnicity, year)",
        "year_range": f"{min(cause_years[key]):.0f}-{max(cause_years[key]):.0f}",
        "observations": int(sum(codes.values())),
        "themes": "Mortality",
    })
print(f"Death causes (canonical by label): {len(cause_codes)}")

# 3. Heat complaint conditions
cond = Counter()
for line in gzip.open(NYC / "data" / "heat-complaints" /
                      "heat-complaints.v1.0.0.records.ndjson.gz", "rt"):
    m = re.search(r'"type":"Complaint".*?"condition":"([^"]*)"', line)
    if m:
        cond[m.group(1)] += 1
for c, n in cond.most_common():
    rows.append({
        "nyc_id": f"complaints:{c}",
        "collection": "heat-complaints",
        "version": vers["heat-complaints"],
        "record_type": "Complaint.condition",
        "label": c,
        "description": f"311 heat-season complaint condition ({n:,} complaints, Oct 2024-Nov 2026)",
        "measurement_type": "complaint count",
        "how_calculated": "",
        "indicator_name": c,
        "icd10": "",
        "geo_types": "borough, ZIP, BBL, lat/lon",
        "year_range": "2024-2026",
        "observations": n,
        "themes": "Heat & temperature; Housing & indoor",
    })
print(f"Complaint conditions: {len(cond)}")

# 4. Tree species
species = {}
for line in gzip.open(NYC / "data" / "street-trees" /
                      "street-trees.v1.0.0.records.ndjson.gz", "rt"):
    if '"type":"Species"' not in line:
        continue
    r = json.loads(line)
    d = r["data"]
    species[r["id"]] = d
for sid, d in sorted(species.items(), key=lambda kv: -kv[1].get("treeCount", 0)):
    rows.append({
        "nyc_id": f"trees:{sid}",
        "collection": "street-trees",
        "version": vers["street-trees"],
        "record_type": "Species",
        "label": d["commonName"],
        "description": f"{d.get('latinName','')} ({d.get('treeCount',0):,} trees, 2015 census)",
        "measurement_type": "tree count",
        "how_calculated": "",
        "indicator_name": d["commonName"],
        "icd10": "",
        "geo_types": "NTA2010, tract, ZIP",
        "year_range": "2015",
        "observations": int(d.get("treeCount", 0)),
        "themes": "Green & built",
    })
print(f"Tree species: {len(species)}")

nyc = pd.DataFrame(rows)
nyc.to_csv(OUT / "nyc_concepts.csv", index=False)
print(f"NYC side: {len(nyc)} concept rows across {nyc.collection.nunique()} collections")

# Skipped surfaces (documented decision)
skipped = {
    "restaurant-inspections": "violation/cuisine text, Manhattan-only sample; no controlled "
                              "concept vocabulary that maps to research constructs (food-safety "
                              "noted qualitatively in the report)",
    "dog-licenses": "5,000-dog sample + 248 breeds; no research-concept surface",
    "geographies": "join hub, not concept-bearing",
}
(OUT / "build_summary.json").write_text(json.dumps({
    "spg_concepts": len(spg_out),
    "spg_domain_rows": len(domains),
    "nyc_concept_rows": len(nyc),
    "nyc_by_collection": nyc.collection.value_counts().to_dict(),
    "death_cause_labels_with_variants": sum(1 for r in rows if r["record_type"] == "CauseOfDeath"
                                            and "variants" in r["description"]),
    "versions": vers,
    "skipped": skipped,
}, indent=2))
print("Wrote mapping/out/{spg_concepts,nyc_concepts}.csv, build_summary.json")
