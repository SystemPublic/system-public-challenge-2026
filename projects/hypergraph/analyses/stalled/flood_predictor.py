"""Claim stalled-flood-zone-starts: do new-building jobs on lots in the 2015 preliminary 1%-annual-chance floodplain
(PLUTO pfirm15_flag = 1) fail to reach a CO within 36 months of their first foundation permit more often than jobs
elsewhere in the same borough?

Jobs: data/derived/stalled/vesting_jobs_union.csv (foundation starts in the windows 15 Dec-14 Jun, 2017-2023, built by
vesting_cohorts.py; outcome stalled_1096 = no CO matched by job number or BBL within 1,096 days). Features: PLUTO
(64uk-42ks, current version) by BBL: pfirm15_flag, firm07_flag, borough, lotarea. Jobs whose BBL is not in current PLUTO
are reported and dropped.

Deciding statistic: Mantel-Haenszel (borough-stratified) risk difference, flood minus non-flood, with a percentile
bootstrap (2,000 draws, seed 20261113, resampling jobs within borough and flood stratum).

Usage: python flood_predictor.py sizes   (feature counts only, no outcome read)
       python flood_predictor.py run
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as so

D = ROOT / "data/derived/stalled"
SEED, DRAWS = 20261113, 2000


def features(bbls):
    rows, srcs = [], []
    bbls = sorted(set(bbls))
    for i in range(0, len(bbls), 150):
        chunk = ",".join(f"'{b}'" for b in bbls[i:i + 150])
        r, src = so.query("64uk-42ks", select="bbl,borough,pfirm15_flag,firm07_flag,lotarea", where=f"bbl in ({chunk})")
        rows += r
        srcs.append(src)
    f = pd.DataFrame(rows)
    f["bbl"] = f.bbl.astype(str).str.replace(r"\.0+$", "", regex=True)
    f["flood"] = (f.pfirm15_flag.fillna("0").astype(str).str.startswith("1")).astype(int)
    return f.drop_duplicates("bbl"), {**srcs[0], "n_queries": len(srcs), "query": {"$where": "bbl in (<job BBLs, 150 per query>)",
                                                                                   "$select": "bbl,borough,pfirm15_flag,firm07_flag,lotarea"}}


def mh(df):
    num = den = 0.0
    for _, g in df.groupby("borough"):
        a, b = g[g.flood == 1], g[g.flood == 0]
        if len(a) == 0 or len(b) == 0:
            continue
        w = len(a) * len(b) / len(g)
        num += w * (a.y.mean() - b.y.mean())
        den += w
    return num / den


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "sizes"
    s = pd.read_csv(D / "vesting_jobs_union.csv", dtype={"bbl": str})
    f, src = features(s.bbl)
    m = s.merge(f, on="bbl", how="inner")
    sizes = dict(jobs=int(len(s)), with_pluto=int(len(m)), flood=int(m.flood.sum()),
                 flood_by_borough=m.groupby("borough").flood.agg(["sum", "size"]).astype(int).to_dict("index"))
    print(json.dumps(sizes, indent=1))
    if mode == "sizes":
        (D / "flood_sizes.json").write_text(json.dumps(sizes, indent=1))
        sys.exit(0)
    m["y"] = m.stalled_1096.astype(int)
    rng = np.random.default_rng(SEED)
    est = mh(m)
    groups = [g for _, g in m.groupby(["borough", "flood"])]
    bs = []
    for _ in range(DRAWS):
        bs.append(mh(pd.concat([g.sample(len(g), replace=True, random_state=rng.integers(2**31)) for g in groups])))
    res = dict(mh_rd=est, lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)),
               crude=dict(flood=float(m[m.flood == 1].y.mean()), other=float(m[m.flood == 0].y.mean())),
               by_borough={b: dict(flood_rate=float(g[g.flood == 1].y.mean()) if g.flood.sum() else None, flood_n=int(g.flood.sum()),
                                   other_rate=float(g[g.flood == 0].y.mean()), other_n=int((g.flood == 0).sum())) for b, g in m.groupby("borough")},
               sizes=sizes, source_pluto=src, seed=SEED, draws=DRAWS)
    print(json.dumps({k: v for k, v in res.items() if k not in ("source_pluto", "sizes")}, indent=1))
    (D / "flood_result.json").write_text(json.dumps(res, indent=1, default=str))
    m[["job", "bbl", "window", "system", "borough", "flood", "lotarea", "y"]].to_csv(D / "flood_jobs.csv", index=False)
