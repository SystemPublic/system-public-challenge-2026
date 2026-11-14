"""New York, exploratory (data already seen): the by-range decomposition with the bicycle
proxy, to set the prediction for a bicycle proxy in Chicago. Reads
data/derived/graph/heat_mechanisms/mediators_daily.csv; writes
data/derived/round2/hot_end/ny_by_range.json."""
import json
from pathlib import Path

import pandas as pd

from analyses.round2.hot_end import model as M

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "derived" / "round2" / "hot_end"
OUT.mkdir(parents=True, exist_ok=True)
d0 = pd.read_csv(ROOT / "data/derived/graph/heat_mechanisms/mediators_daily.csv", index_col=0, parse_dates=True).dropna(subset=["TMAX"])
res = {"label": "exploratory; New York data already seen"}
for p in ("bike", "noise_street"):
    d = d0.dropna(subset=[p]).copy()
    a = M.nb_alpha("n", d)
    w0, _ = M.curve_fit(d, "n", a)
    w1, _ = M.curve_fit(d, "n", a, p)
    pa = M.nb_alpha(p, d, default=0.1)
    pc, _ = M.curve_fit(d, p, pa)
    res[p] = {"n_days": len(d), "alpha": a, "shootings_without": w0, "shootings_with": w1, "proxy_curve": pc,
              "shares": M.shares(d, "n", p, a, boot=300)}
(OUT / "ny_by_range.json").write_text(json.dumps(res, indent=1))
for p in ("bike", "noise_street"):
    r = res[p]
    print(p, r["n_days"])
    for k in ("rr_21_vs_15", "rr_33_vs_27"):
        print("  ", k, "proxy", [round(r["proxy_curve"][k][x], 3) for x in ("estimate", "lo", "hi")],
              "shoot", [round(r["shootings_without"][k][x], 3) for x in ("estimate", "lo", "hi")],
              "with", [round(r["shootings_with"][k][x], 3) for x in ("estimate", "lo", "hi")])
    for k, v in r["shares"].items():
        print("  ", k, [round(v[x], 2) for x in ("estimate", "lo", "hi")])
