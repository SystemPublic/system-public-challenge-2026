"""EXPLORATORY (not registered): ratio of the 2026 ratio of ratios to the placebo-year ratio of ratios,
with a joint cluster bootstrap over treated sites. Needs the matched sets of both analyses, so it
rebuilds them from the cached crash data with rlc_did's own functions."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analyses/street_safety"))
import rlc_did as R

treated, allc, _ = R.load_sites()
pool = R.control_pool(allc)
rows, _ = R.fetch_crashes()
cx, cy, cym, vals = R.crash_arrays(rows)
real = R.build(treated, pool, cx, cy, cym, vals)
plac = R.placebo(treated, pool, cx, cy, cym, vals)
rng = np.random.default_rng(20261113)
n = len(real)
out = {}
for o in R.OUTCOMES:
    est = R.rr_from(real, o)[0] / R.rr_from(plac, o)[0]
    bs = []
    for _ in range(2000):
        w = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        a, b = R.rr_from(real, o, w)[0], R.rr_from(plac, o, w)[0]
        if np.isfinite(a) and np.isfinite(b) and b > 0:
            bs.append(a / b)
    out[o] = {"ratio": round(est, 3), "lo": round(float(np.percentile(bs, 2.5)), 3), "hi": round(float(np.percentile(bs, 97.5)), 3)}
# monthly treated/control ratio for the February 2026 cohort, Jan 2023 - Oct 2026 (all crashes)
feb = [i for i, t in enumerate(sorted(treated, key=lambda s: s["first"])) if t["first"] == "2026-02"]
tr = sorted(treated, key=lambda s: s["first"])
months = [y * 100 + m for y in (2023, 2024, 2025, 2026) for m in range(1, 13) if y * 100 + m <= 202610]
from scipy.spatial import cKDTree
tree = cKDTree(np.c_[cx, cy])
def series(points):
    s = {m: {k: 0.0 for k in R.OUTCOMES} for m in months}
    for px, py in points:
        for j in tree.query_ball_point([px, py], R.R_M):
            if cym[j] in s:
                for k in R.OUTCOMES:
                    s[cym[j]][k] += vals[k][j]
    return s
tpts = [tuple(map(float, R.xy(tr[i]["lat"], tr[i]["lon"]))) for i in feb]
names = {f"{r['a']} @ {r['b']}": r for r in pool}
cpts = []
for i in feb:
    for nm in real[i]["control_names"]:
        r = names.get(nm)
        if r:
            cpts.append(tuple(map(float, R.xy(r["lat"], r["lon"]))))
ts, cs = series(tpts), series(cpts)
mon = [{"ym": m, "treated_all": ts[m]["all"], "control_all_per_site": cs[m]["all"] / max(len(cpts), 1) * len(tpts),
        "treated_rear": ts[m]["rear_end"], "control_rear_per_site": cs[m]["rear_end"] / max(len(cpts), 1) * len(tpts)} for m in months]
res = {"label": "exploratory", "placebo_adjusted": out, "feb2026_cohort": {"n_sites": len(feb), "n_controls": len(cpts), "monthly": mon}}
(ROOT / "data/derived/street_safety/exploratory_placebo_adjusted.json").write_text(json.dumps(res, indent=1))
print(json.dumps(out, indent=1))
