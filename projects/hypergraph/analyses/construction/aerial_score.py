"""Claim construction-aerial-triangulation, step 2: join CO status to the blind judgements and score.
Writes data/derived/construction/aerial_scored.csv and aerial_summary.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "construction"


def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


s = pd.read_csv(D / "aerial_sample.csv", dtype={"job": str})
j = pd.read_csv(D / "aerial_judgements.csv")
nj = pd.read_csv(D / "nb_jobs.csv.gz", dtype={"job": str})
for c in ("first_permit", "first_co"):
    nj[c] = pd.to_datetime(nj[c], format="mixed", errors="coerce")
x = s.merge(j, on="idx").merge(nj[["job", "first_permit", "first_co", "final_co"]], on="job", how="left")
x["img_date"] = pd.to_datetime(x.date_2022)
x["has_co_by_2022"] = x.first_co.notna() & (x.first_co <= x.img_date)
x["has_co_now"] = x.first_co.notna()
x.to_csv(D / "aerial_scored.csv", index=False)

out = {"n": int(len(x)), "judgement_counts": x.judgement.value_counts().to_dict()}
out["share_changed_all"] = float((x.judgement == "changed").mean())
dec = x[x.judgement != "unclear"]
out["share_changed_of_decided"] = float((dec.judgement == "changed").mean())
out["crosstab_all"] = pd.crosstab(x.judgement, x.has_co_by_2022).to_dict()
ch = x.judgement == "changed"
out["kappa_changed_vs_co_by_2022_unclear_as_unchanged"] = float(kappa(ch, x.has_co_by_2022))
out["kappa_changed_vs_co_by_2022_decided_only"] = float(kappa(dec.judgement == "changed", dec.has_co_by_2022))
out["share_changed_without_co_by_2022"] = float((ch & ~x.has_co_by_2022).mean())
out["share_co_but_not_changed"] = float((~ch & x.has_co_by_2022).mean())
out["share_co_but_unchanged_strict"] = float(((x.judgement == "unchanged") & x.has_co_by_2022).mean())
out["share_changed_and_co_now"] = float((ch & x.has_co_now).mean())
out["co_by_2022_share"] = float(x.has_co_by_2022.mean())
out["co_now_share"] = float(x.has_co_now.mean())
out["mad_z_by_judgement"] = x.groupby("judgement").mad_z.median().round(3).to_dict()
# pixel score as a secondary classifier: best threshold against the visual judgement on decided pairs
best = max(((t, ((dec.mad_z > t) == (dec.judgement == "changed")).mean()) for t in np.arange(0.6, 1.5, 0.05)), key=lambda z: z[1])
out["mad_threshold_best_vs_visual"] = {"threshold": round(float(best[0]), 2), "accuracy": round(float(best[1]), 3)}
out["mad_auc_vs_visual"] = float(pd.Series(dec.mad_z.values).rank().pipe(
    lambda r: (r[(dec.judgement == "changed").values].sum() - (dec.judgement == "changed").sum() * ((dec.judgement == "changed").sum() + 1) / 2)
    / ((dec.judgement == "changed").sum() * (dec.judgement != "changed").sum())))
out["image_dates_2022"] = sorted(x.date_2022.unique().tolist())
out["image_dates_2017"] = sorted(x.date_2017.unique().tolist())
(D / "aerial_summary.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
print(x[["idx", "judgement", "has_co_by_2022", "has_co_now", "first_permit", "first_co", "mad_z"]].to_string())
