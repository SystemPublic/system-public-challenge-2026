#!/usr/bin/env python3
"""Assemble the final concept map from tier-0 anchors + LLM adjudications.

Inputs: mapping/out/{spg_concepts,nyc_concepts,tier0_anchors}.csv,
        mapping/out/adjudications_*.jsonl   (written during the LLM pass)
Outputs: mapping/out/concept_map.csv, review_queue.csv, unmatched_nyc.csv, report.md
Run: python3 -I mapping/make_outputs.py
"""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "mapping" / "out"

spg = pd.read_csv(OUT / "spg_concepts.csv").fillna("")
nyc = pd.read_csv(OUT / "nyc_concepts.csv").fillna("")
# adjudications may reference any of the 45,721 concepts, not just the 473
full = pd.read_csv(BASE / "dataverse_files" /
                   "system-public-graph-v1-concepts-1.csv", dtype=str).fillna("")
full["domains"] = ""
dom473 = dict(zip(spg.system_id, spg.domains))
full["domains"] = full.system_id.map(dom473).fillna("")
spg_by_id = full.set_index("system_id")[["wikidata_id", "wikidata_label",
                                         "domains"]].rename(columns={
    "wikidata_label": "label"}).to_dict("index")
nyc_by_id = nyc.set_index("nyc_id").to_dict("index")

manifest = json.loads((BASE / "dataverse_files" / "MANIFEST.json").read_text())
concepts_sha = next(f["checksums"]["sha256"][:12] for f in manifest["files"]
                    if "concepts" in f["filename"])
versions = json.loads((OUT / "build_summary.json").read_text())["versions"]
VERSION = (f"SPG v1 concepts sha256:{concepts_sha}; NYC "
           + "; ".join(f"{k} {v.split(' (')[0]}" for k, v in versions.items()
                       if k != "geographies"))

rows = []

# ---- tier-0 anchors (deterministic, method=anchor) ----
anchors = pd.read_csv(OUT / "tier0_anchors.csv").fillna("")

# LLM-pass rejections of noisy anchors: {"action":"reject_anchor", ...}
reject_pairs = set()
for f in sorted(OUT.glob("adjudications_*.jsonl")):
    for line in f.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            d = json.loads(line)
            if d.get("action") == "reject_anchor":
                reject_pairs.add((d["nyc_id"], d["spg_system_id"]))

for a in anchors.itertuples():
    n = nyc_by_id.get(a.nyc_id)
    if not n:
        continue
    if (a.nyc_id, a.spg_system_id) in reject_pairs:
        continue
    rows.append({
        "nyc_id": a.nyc_id, "spg_system_id": a.spg_system_id,
        "spg_label": a.spg_label, "spg_domains": "", "match_type": "equivalent",
        "confidence": "high", "method": "anchor",
        "rationale": (f"ICD-10 [{a.matched_token}] on Wikidata {a.qid} ({a.wd_label}); "
                      f"that Wikidata item is SPG concept '{a.spg_label}'"),
    })

# ---- LLM adjudications ----
llm_rows = []
for f in sorted(OUT.glob("adjudications_*.jsonl")):
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        d = json.loads(line)
        if d.get("action"):  # control entries (e.g. reject_anchor)
            continue
        llm_rows.append(d)

for r in llm_rows:
    n = nyc_by_id.get(r["nyc_id"])
    s = spg_by_id.get(r["spg_system_id"])
    if not n or not s:
        raise SystemExit(f"unknown id in adjudications: {r}")
    rows.append({
        "nyc_id": r["nyc_id"], "spg_system_id": r["spg_system_id"],
        "spg_label": s["label"], "spg_domains": s["domains"],
        "match_type": r["match_type"], "confidence": r["confidence"],
        "method": "llm", "rationale": r["rationale"],
    })

# dedupe (anchor + llm can land on the same pair; llm wins as more specific)
df = pd.DataFrame(rows).drop_duplicates(subset=["nyc_id", "spg_system_id"],
                                        keep="last")
df["versions"] = VERSION

# enrich with NYC context
df = df.merge(nyc[["nyc_id", "collection", "record_type", "label", "description",
                   "measurement_type", "year_range"]]
              .rename(columns={"label": "nyc_label",
                               "description": "nyc_description"}),
              on="nyc_id", how="left")
df = df[["nyc_id", "collection", "record_type", "nyc_label", "nyc_description",
         "measurement_type", "year_range", "spg_system_id", "spg_label",
         "spg_domains", "match_type", "confidence", "method", "rationale",
         "versions"]]
df = df.sort_values(["collection", "nyc_id", "match_type"]).reset_index(drop=True)
df.to_csv(OUT / "concept_map.csv", index=False)

# ---- review queue ----
in_queue = df[(df.confidence == "low")
              | ((df.confidence == "medium") & (df.match_type == "related-component"))]
in_queue.to_csv(OUT / "review_queue.csv", index=False)

# ---- unmatched NYC rows ----
matched_ids = set(df.nyc_id)
unmatched = nyc[~nyc.nyc_id.isin(matched_ids)].copy()
unmatched["note"] = "no SPG concept matched by anchor or LLM pass"
unmatched.to_csv(OUT / "unmatched_nyc.csv", index=False)

# ---- report ----
n_rows = len(nyc)
cov = df.groupby("collection").nyc_id.nunique()
sizes = nyc.groupby("collection").size()
lines = [
    "# Concept Map Report",
    "",
    f"SPG matching universe: {len(spg)} challenge-domain concepts "
    "(+ lexical supplements from the full 45,721-concept set).",
    f"NYC concept rows: {n_rows}.",
    "",
    "## Coverage",
    "",
    "| collection | NYC rows | with >=1 SPG match | coverage |",
    "|---|---|---|---|",
]
for coll in sizes.index:
    c = cov.get(coll, 0)
    lines.append(f"| {coll} | {sizes[coll]} | {c} | {c / sizes[coll]:.0%} |")
tot_c = df.nyc_id.nunique()
lines.append(f"| **total** | {n_rows} | {tot_c} | {tot_c / n_rows:.0%} |")
lines += ["", f"Match rows: {len(df)} (many-to-many).", "",
          "By match type:", ""]
for k, v in df.match_type.value_counts().items():
    lines.append(f"- {k}: {v}")
lines += ["", "By method:", ""]
for k, v in df.method.value_counts().items():
    lines.append(f"- {k}: {v}")
lines += ["", f"Review queue: {len(in_queue)} rows (low confidence, or medium "
              f"related-component) -> review_queue.csv", "",
          f"Unmatched NYC rows: {len(unmatched)} -> unmatched_nyc.csv "
          "(seed for the research-needed map)", "",
          "Every row cites: " + VERSION, ""]
(OUT / "report.md").write_text("\n".join(lines))
print(f"concept_map.csv: {len(df)} rows ({tot_c}/{n_rows} NYC rows matched, "
      f"{len(in_queue)} in review queue, {len(unmatched)} unmatched)")
