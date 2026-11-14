"""List the inspections whose score differs between the June snapshot and the November table.

Usage: python -m analyses.underlay_drift.changed_scores
Reads the match table built by analyses/underlay_drift/compare.py (kept outside the repository) and the snapshot's
Restaurant records, and writes data/derived/underlay_drift/changed_scores.json for viz/inspections.html.
Written on 14 November 2026.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
U = Path.home() / "opt" / "nyc-concordance" / "underlay"


def main() -> None:
    m = pd.read_csv(U / "inspection_match.csv.gz", low_memory=False)
    c = m[(m.status == "both") & (m.d_score.astype(str).isin(["True", "1", "1.0"]))].copy()
    c["drop"] = c.score_s - c.score_l
    band = lambda s: np.where(s <= 13, "A", np.where(s <= 27, "B", "C"))  # noqa: E731
    c["band_s"], c["band_l"] = band(c.score_s), band(c.score_l)
    names = {}
    for line in open(U / "records_v1.0.0.ndjson"):
        r = json.loads(line)
        if r["type"] == "Restaurant":
            d = r["data"]
            names[str(r["id"])] = {"name": d.get("name"), "street": " ".join((str(d.get("building") or "") + " " + str(d.get("street") or "")).split()), "zip": d.get("zipcode")}
    rows = []
    for _, r in c.sort_values(["drop", "inspectionDate_s"], ascending=[False, False]).iterrows():
        cam = str(int(r.camis_s)); n = names.get(cam, {})
        rows.append({"id": r["_id"], "camis": cam, "name": n.get("name"), "street": n.get("street"), "zip": n.get("zip"), "date": r.inspectionDate_s,
                     "score_june": int(r.score_s), "score_nov": int(r.score_l), "band_june": str(r.band_s), "band_nov": str(r.band_l)})
    st = m.status.value_counts().to_dict()
    out = {"note": "Inspections present in both copies whose score differs (analyses/underlay_drift/changed_scores.py; method in docs/underlay_drift.md). Score bands: 0 to 13 is the A range, 14 to 27 the B range, 28 and over the C range.",
           "june": {"owner": "nyc", "slug": "restaurant-inspections", "version": "v1.0.0", "label": "June 2026"},
           "november": {"owner": "system-community", "slug": "nyc-restaurant-inspections-2026-11", "version": "v1.0.0", "label": "November 2026"},
           "counts": {"in_both": int(st.get("both", 0)), "june_only": int(st.get("snapshot only", 0)), "november_only": int(st.get("live only", 0)),
                      "scores_changed": len(c), "scores_fell": int((c["drop"] > 0).sum()), "scores_rose": int((c["drop"] < 0).sum()), "median_drop": float(c["drop"].median()),
                      "band_changed": int((c.band_s != c.band_l).sum()), "into_A_range": int(((c.score_s >= 14) & (c.score_l <= 13)).sum()), "restaurants_gone": 519},
           "rows": rows}
    (ROOT / "data/derived/underlay_drift/changed_scores.json").write_text(json.dumps(out, indent=0))
    print(json.dumps(out["counts"]))


if __name__ == "__main__":
    main()
