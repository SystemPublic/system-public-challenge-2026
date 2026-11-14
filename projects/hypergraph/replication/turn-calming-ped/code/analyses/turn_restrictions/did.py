"""Registered test of NYC DOT left-turn traffic calming (claims turn-calming-ped, turn-calming-leftturn,
turn-calming-displacement). Fixed with the registrations; no resampling, so no seed.

Treatment: data/derived/turn_restrictions/sites.json (sm2x-35i7, left-turn records merged within 40 m,
earliest date kept). Outcomes from ~/opt/nyc-concordance/turn_restrictions/ (fetch_crashes.py):
  ped     pedestrians injured or killed (h9gi-nx95 number_of_pedestrians_injured + _killed) in crashes
          within 40 m of the site
  lt      crashes within 40 m with at least one vehicle whose pre_crash is 'Making Left Turn' (bm4k-52h4)
  *_ring  the same counts 50-200 m from the site, excluding crashes within 40 m of any other calming site
Design: stacked cohorts by install quarter, 2016Q3-2023Q2. Treated: sites installed in the quarter, with
their own install month t0; pre = months t0-24..t0-1, post = t0+1..t0+24 (install month dropped).
Controls: sites whose install month is later than the cohort's last month + 24 (not yet treated in any
window), given the cohort's middle month as t0. Post windows must end by END.
Model: conditional Poisson as a binomial GLM, post ~ Binomial(pre+post, p), logit p = cohort + b*treated;
exp(b) is the ratio of ratios (treated post/pre over control post/pre). Standard errors clustered by site
(controls recur across cohorts). 95% Wald interval.
Non-deciding checks: 30 m radius; cohorts whose windows avoid Mar-Jun 2020; event-time series for the figure."""
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analyses/turn_restrictions"))
from sites import xy  # noqa: E402

OPT = Path.home() / "opt/nyc-concordance/turn_restrictions"
OUT = ROOT / "data/derived/turn_restrictions"
END = 2026 * 12 + 8  # last month used: September 2026 (month index = year*12 + month-1)
R_IN, R1, R2 = 40.0, 50.0, 200.0
OUTCOMES = ["ped", "lt", "ped_ring", "lt_ring"]


def mi(d):
    return int(d[:4]) * 12 + int(d[5:7]) - 1


def load_crashes():
    left = set()
    with (OPT / "left_vehicles.csv").open() as f:
        for r in csv.DictReader(f):
            left.add(r["collision_id"])
    X, Y, M, PED, LT = [], [], [], [], []
    with (OPT / "crashes.csv").open() as f:
        for r in csv.DictReader(f):
            try:
                lat, lon = float(r["latitude"]), float(r["longitude"])
            except (TypeError, ValueError):
                continue
            if not (40.45 < lat < 40.95 and -74.3 < lon < -73.65):
                continue
            x, y = xy(lat, lon)
            X.append(x); Y.append(y); M.append(mi(r["crash_date"]))
            PED.append(int(r["number_of_pedestrians_injured"] or 0) + int(r["number_of_pedestrians_killed"] or 0))
            LT.append(1 if r["collision_id"] in left else 0)
    return np.array(X), np.array(Y), np.array(M), np.array(PED), np.array(LT), len(left)


def site_monthly(sites, X, Y, M, PED, LT, r_in=R_IN):
    from scipy.spatial import cKDTree
    tree = cKDTree(np.c_[X, Y])
    spts = np.array([[s["x"], s["y"]] for s in sites])
    stree = cKDTree(spts)
    # crashes within r_in of any site
    near_any = np.zeros(len(X), bool)
    for idx in tree.query_ball_point(spts, r_in):
        near_any[idx] = True
    counts = []
    for k, s in enumerate(sites):
        c = {o: defaultdict(int) for o in OUTCOMES}
        inner = tree.query_ball_point([s["x"], s["y"]], r_in)
        for i in inner:
            c["ped"][M[i]] += PED[i]
            c["lt"][M[i]] += LT[i]
        outer = tree.query_ball_point([s["x"], s["y"]], R2)
        for i in outer:
            d = math.hypot(X[i] - s["x"], Y[i] - s["y"])
            if d < R1 or near_any[i]:
                continue
            c["ped_ring"][M[i]] += PED[i]
            c["lt_ring"][M[i]] += LT[i]
        counts.append(c)
    return counts


def window(c, t0):
    pre = sum(v for m, v in c.items() if t0 - 24 <= m <= t0 - 1)
    post = sum(v for m, v in c.items() if t0 + 1 <= m <= t0 + 24)
    return pre, post


def stack(sites, counts, outcome, avoid_2020=False):
    rows = []
    t_inst = [mi(s["date"]) for s in sites]
    for q in range(2016 * 4 + 2, 2023 * 4 + 2):  # 2016Q3 .. 2023Q2
        m0, m2 = q * 3, q * 3 + 2
        tr = [k for k, t in enumerate(t_inst) if m0 <= t <= m2 and t + 24 <= END]
        if not tr:
            continue
        if avoid_2020 and not (m2 + 24 < 2020 * 12 + 2 or m0 - 24 > 2020 * 12 + 5):
            continue
        ctl = [k for k, t in enumerate(t_inst) if t > m2 + 24]
        if not ctl:
            continue
        for k in tr:
            pre, post = window(counts[k][outcome], t_inst[k])
            rows.append((q, k, 1, pre, post))
        for k in ctl:
            pre, post = window(counts[k][outcome], m0 + 1)
            rows.append((q, k, 0, pre, post))
    return rows


def fit(rows):
    import pandas as pd
    import statsmodels.api as sm
    df = pd.DataFrame(rows, columns=["cohort", "site", "treated", "pre", "post"])
    df = df[df.pre + df.post > 0].copy()
    n = df.pre + df.post
    Xd = pd.get_dummies(df.cohort.astype(str), prefix="c", drop_first=False).astype(float)
    Xd["treated"] = df.treated.astype(float)
    mod = sm.GLM(df.post / n, Xd, family=sm.families.Binomial(), var_weights=n)
    res = mod.fit(cov_type="cluster", cov_kwds={"groups": df.site.values})
    b, se = res.params["treated"], res.bse["treated"]
    t = df[df.treated == 1]
    c = df[df.treated == 0]
    return {"ror": round(math.exp(b), 4), "lo": round(math.exp(b - 1.96 * se), 4),
            "hi": round(math.exp(b + 1.96 * se), 4), "log_ror": round(b, 4), "se_log": round(se, 4),
            "n_rows": int(len(df)), "n_treated_sites": int(t.site.nunique()), "n_control_sites": int(c.site.nunique()),
            "n_cohorts": int(df.cohort.nunique()),
            "treated_pre": int(t.pre.sum()), "treated_post": int(t.post.sum()),
            "control_pre_rows_sum": int(c.pre.sum()), "control_post_rows_sum": int(c.post.sum())}


def event_series(sites, counts, outcome):
    """Totals by event month for treated sites (own t0) and for controls stacked as in the design."""
    t_inst = [mi(s["date"]) for s in sites]
    T = defaultdict(float); C = defaultdict(float); nC = defaultdict(float)
    for q in range(2016 * 4 + 2, 2023 * 4 + 2):
        m0, m2 = q * 3, q * 3 + 2
        tr = [k for k, t in enumerate(t_inst) if m0 <= t <= m2 and t + 24 <= END]
        ctl = [k for k, t in enumerate(t_inst) if t > m2 + 24]
        if not tr or not ctl:
            continue
        for e in range(-24, 25):
            for k in tr:
                T[e] += counts[k][outcome].get(t_inst[k] + e, 0)
            # controls scaled to the number of treated sites in the cohort
            tot = sum(counts[k][outcome].get(m0 + 1 + e, 0) for k in ctl)
            C[e] += tot * len(tr) / len(ctl)
    return {e: (T[e], C[e]) for e in range(-24, 25)}


def main():
    sites = json.loads((OUT / "sites.json").read_text())["sites"]
    X, Y, M, PED, LT, nleft = load_crashes()
    counts = site_monthly(sites, X, Y, M, PED, LT)
    res = {"n_crashes_geocoded": int(len(X)), "n_left_turn_collision_ids": nleft, "end_month": "2026-09",
           "primary": {}, "checks": {}}
    for o in OUTCOMES:
        res["primary"][o] = fit(stack(sites, counts, o))
        res["checks"][o + "_avoid2020"] = fit(stack(sites, counts, o, avoid_2020=True))
    counts30 = site_monthly(sites, X, Y, M, PED, LT, r_in=30.0)
    for o in ["ped", "lt"]:
        res["checks"][o + "_r30"] = fit(stack(sites, counts30, o))
    res["event"] = {o: {str(e): [round(a, 2), round(b, 2)] for e, (a, b) in event_series(sites, counts, o).items()}
                    for o in OUTCOMES}
    (OUT / "did_results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({"primary": res["primary"], "checks": res["checks"]}, indent=1))


if __name__ == "__main__":
    main()
