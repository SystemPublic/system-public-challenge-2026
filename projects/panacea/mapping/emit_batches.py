#!/usr/bin/env python3
"""Emit compact adjudication batch files for the in-session LLM matching pass.

Two batches:
  batch1_ehdp.md                  - 378 EHDP challenge measures vs SPG-473
  batch2_deaths_complaints_trees.md - 31 death causes (+ tier-0 anchor results),
                                      4 complaint conditions, 132 tree species
Each batch embeds:
  - the full SPG-473 table (system_id | label | description | aliases | domains)
  - NYC rows with their context fields
  - "supplement candidates": lexical top-3 matches from the FULL 45,721 SPG
    concepts (TF-IDF char n-grams) that are NOT already in SPG-473, grouped per
    indicator family / per row — so recall does not depend on the 473 alone.
Run: python3 -I mapping/emit_batches.py
"""
import json
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "mapping" / "out"
BATCHES = OUT / "batches"
BATCHES.mkdir(parents=True, exist_ok=True)

spg = pd.read_csv(OUT / "spg_concepts.csv").fillna("")
nyc = pd.read_csv(OUT / "nyc_concepts.csv").fillna("")
full = pd.read_csv(BASE / "dataverse_files" /
                   "system-public-graph-v1-concepts-1.csv", dtype=str).fillna("")

# ---------------------------------------------------------------- SPG tables
def spg_table(df):
    lines = ["| system_id | wikidata_id | label | description | aliases | domains |",
             "|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        lines.append(f"| {r.system_id} | {r.wikidata_id} | {r.label} | "
                     f"{str(r.description)[:90]} | {str(r.aliases)[:60]} | {r.domains} |")
    return "\n".join(lines)


# ---------------------------------------------------------------- supplements
full["text"] = (full.wikidata_label + " " + full.wikidata_aliases.str.replace('"', ' ')
                + " " + full.wikidata_description.str.slice(0, 120))
in473 = set(spg.system_id)
# Candidate pool = concepts OUTSIDE the 473 (those are already in the batch table).
pool = full[~full.system_id.isin(in473)].reset_index(drop=True)
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2,
                      sublinear_tf=True)
X_pool = vec.fit_transform(pool.text)


def supplement_candidates(query_text: str, k=3, floor=0.22):
    if not query_text.strip():
        return []
    q = vec.transform([query_text])
    sims = cosine_similarity(q, X_pool)[0]
    idx = sims.argsort()[::-1][:k]
    out = []
    for i in idx:
        if sims[i] >= floor:
            r = pool.iloc[i]
            out.append((r.system_id, r.wikidata_label, r.wikidata_description[:70],
                        round(float(sims[i]), 2)))
    return out


def fam_label(measure_name: str) -> str:
    return measure_name.split(",")[0].strip()  # "<label>, <measurementType>"


# ---------------------------------------------------------------- batch 1: EHDP
ehdp = nyc[nyc.collection == "environment-health"].copy()
ehdp["fam"] = ehdp.label.map(fam_label)
fams = {}
for _, r in ehdp.iterrows():
    fams.setdefault(r.fam, []).append(r)

supp_by_fam = {f: supplement_candidates(f) for f in fams}
lines = [
    "# Batch 1/2 — EHDP challenge measures vs SPG concepts",
    "",
    "For every NYC row below, decide whether an SPG concept maps to it.",
    "Match types: `equivalent` (same construct), `broader-narrower` (construct covers the",
    "measure or vice versa — e.g. 'asthma' vs 'Asthma ED visits, Number'), `related-component`",
    "(same topic, different construct — e.g. 'heat wave' vs 'Heat ED visits'), `no-match`.",
    "Confidence: high / medium / low. Do NOT write no-match rows — every NYC id absent from",
    "your output is treated as no-match. Only emit rows with a match.",
    "SPG concepts here are the 473 challenge-domain ones; the supplement lists add lexical",
    "candidates from the wider 45,721-concept set (outside the 473). You may also name any",
    "other SPG concept you believe exists — only supplement-listed and table-listed ids are",
    "guaranteed real.",
    "",
    "## SPG-473 concepts (the matching universe)",
    "",
    spg_table(spg),
    "",
]
for fam in sorted(fams, key=lambda f: -len(fams[f])):
    rows = fams[fam]
    lines.append(f"\n## NYC family: {fam}  ({len(rows)} measures)")
    lines.append("")
    lines.append("| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r.nyc_id} | {r.label} | {r.measurement_type} | "
                     f"{str(r.description)[:80]} | {str(r.how_calculated)[:60]} | "
                     f"{r.themes} | {r.year_range} |")
    supp = supp_by_fam.get(fam, [])
    if supp:
        lines.append("")
        lines.append("Supplement candidates (wider SPG, not in table above):")
        for sid, lab, desc, sc in supp:
            lines.append(f"- `{sid}` {lab} — {desc} (cos {sc})")

(BATCHES / "batch1_ehdp.md").write_text("\n".join(lines))
print(f"batch1_ehdp.md: {len(ehdp)} NYC rows, {len(spg)} SPG, "
      f"{sum(1 for v in supp_by_fam.values() if v)} families with supplements")

# ---------------------------------------------------------------- batch 2
anchors = pd.read_csv(OUT / "tier0_anchors.csv").fillna("") \
    if (OUT / "tier0_anchors.csv").exists() else pd.DataFrame()
wd_only = pd.read_csv(OUT / "tier0_wikidata_only.csv").fillna("") \
    if (OUT / "tier0_wikidata_only.csv").exists() else pd.DataFrame()
unmatched = json.loads((OUT / "tier0_unmatched.json").read_text()) \
    if (OUT / "tier0_unmatched.json").exists() else []

rest = nyc[nyc.collection != "environment-health"].copy()
rest["supp"] = rest.apply(lambda r: supplement_candidates(
    f"{r.label} {r.description}", k=2, floor=0.25), axis=1)

lines = [
    "# Batch 2/2 — death causes, complaint conditions, tree species vs SPG",
    "",
    "Same rules as batch 1. Death causes already carry Tier-0 Wikidata anchors",
    "(ICD-10 verified) — accept them into your output with method=anchor unless you",
    "believe an anchor is wrong; add any additional SPG concept matches as method=llm.",
    "For tree species, expect mostly no-match: only match where an SPG concept clearly",
    "refers to the species or to species-level health concepts.",
    "",
    "## SPG-473 concepts (the matching universe)",
    "",
    spg_table(spg),
    "",
    "## NYC rows",
    "",
]
for coll in ["leading-causes-of-death", "heat-complaints", "street-trees"]:
    sub = rest[rest.collection == coll]
    lines.append(f"\n### {coll} ({len(sub)})")
    lines.append("")
    lines.append("| nyc_id | label | description | measurementType | years |")
    lines.append("|---|---|---|---|---|")
    for r in sub.itertuples():
        lines.append(f"| {r.nyc_id} | {r.label} | {str(r.description)[:80]} | "
                     f"{r.measurement_type} | {r.year_range} |")
    if coll == "leading-causes-of-death":
        if len(anchors):
            an = anchors.merge(nyc[["nyc_id", "label"]].rename(columns={"label": "cause"}),
                               on="nyc_id", how="left")
            lines.append("")
            lines.append("### Tier-0 anchors (ICD-10 -> Wikidata -> SPG, verified)")
            lines.append("")
            lines.append("| nyc_id | cause | SPG system_id | SPG label | wd item | matched ICD | method | in-473 |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for a in an.itertuples():
                lines.append(f"| {a.nyc_id} | {a.cause} | {a.spg_system_id} | "
                             f"{a.spg_label} | {a.qid} {a.wd_label} | {a.matched_token} | "
                             f"{a.method} | {a.spg_in_challenge_domains} |")
        if len(wd_only):
            wo = wd_only.merge(nyc[["nyc_id", "label"]].rename(columns={"label": "cause"}),
                               on="nyc_id", how="left")
            lines.append("")
            lines.append("### Verified on Wikidata but NOT in SPG (context only — cannot be matches)")
            lines.append("")
            for w in wo.itertuples():
                lines.append(f"- {w.cause}: {w.qid} {w.wd_label} ({w.matched_token})")
        if unmatched:
            lines.append("")
            lines.append("### Causes with NO verified Wikidata candidate (need LLM matching)")
            lines.append("")
            for u in unmatched:
                lines.append(f"- {u['nyc_id']} {u['cause']} (ICD: {','.join(u['icd10'])})")
    supp_rows = [(r.nyc_id, r.supp) for r in rest[rest.collection == coll].itertuples()
                 if r.supp]
    if supp_rows:
        lines.append("")
        lines.append("Supplement candidates (wider SPG, not in table above):")
        for nyc_id, supp in supp_rows:
            for sid, lab, desc, sc in supp:
                lines.append(f"- {nyc_id} -> `{sid}` {lab} — {desc} (cos {sc})")

(BATCHES / "batch2_deaths_complaints_trees.md").write_text("\n".join(lines))
print(f"batch2: {len(rest)} NYC rows, anchors={len(anchors)}, "
      f"wd_only={len(wd_only)}, unmatched={len(unmatched)}")
