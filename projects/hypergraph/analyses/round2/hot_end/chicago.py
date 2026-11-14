"""transfer-chicago-hot-end: the registered test. Registered in
claims/registered/transfer-chicago-hot-end.json before any Divvy value was queried.
Run: ~/.venvs/nyc-concordance/bin/python -m analyses.round2.hot_end.chicago
Writes data/derived/round2/hot_end/: divvy_daily.csv, chicago_daily.csv, results.json,
curves.csv, sources.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import concord.socrata as soc
from analyses.round2.hot_end import model as M

soc.DOMAIN = "https://data.cityofchicago.org"
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "derived" / "round2" / "hot_end"
W0, W1 = "2013-07-01", "2019-12-31"
r3 = lambda v: {k: v[k] for k in ("estimate", "lo", "hi")}


def divvy():
    # one query per month: a whole year grouped by day and user type times out on the portal
    rows, srcs = [], []
    for m in pd.period_range("2013-06", "2019-12", freq="M"):
        r, s = soc.query_all("fg6s-gzvg", select="date_trunc_ymd(start_time) as d, user_type, count(*) as n",
                             where=f"start_time between '{m.start_time:%Y-%m-%d}T00:00:00' and '{m.end_time:%Y-%m-%d}T23:59:59'",
                             group="d, user_type", order="d, user_type")
        rows += r
        srcs.append(s)
    f = pd.DataFrame(rows)
    f["d"], f["n"] = pd.to_datetime(f["d"]), f["n"].astype(int)
    w = f.pivot_table(index="d", columns="user_type", values="n", aggfunc="sum").fillna(0)
    idx = pd.date_range(W0, W1, freq="D")
    w = w.reindex(idx).fillna(0)
    out = pd.DataFrame({"trips": w.sum(axis=1), "customer": w.get("Customer", 0), "subscriber": w.get("Subscriber", 0)}, index=idx)
    out.index.name = "date"
    return out, srcs


def fit_all(d, y, proxy=None):
    a = M.nb_alpha(y, d, default=0.1)
    c, cur = M.curve_fit(d, y, a, proxy)
    return {"alpha": a, "n_days": int(len(d)), **{k: (r3(v) if "estimate" in v and "lo" in v else v) for k, v in c.items()}}, cur


def main():
    dv, srcs = divvy()
    dv.to_csv(OUT / "divvy_daily.csv")
    full = pd.read_csv(ROOT / "data/derived/graph/transfer_chicago/chicago_heat_daily.csv", index_col=0, parse_dates=True).dropna(subset=["TMAX"])
    win = full.loc[W0:W1].join(dv)
    win["ym"] = win["year"].astype(str) + "-" + win["month"].astype(str)
    win.to_csv(OUT / "chicago_daily.csv")
    res = {"divvy_window": [W0, W1], "n_days_window": int(len(win)), "n_days_full": int(len(full)),
           "divvy": {"trips_total": int(win.trips.sum()), "zero_days": int((win.trips == 0).sum()),
                     "median_per_day": float(win.trips.median()), "customer_share": float(win.customer.sum() / win.trips.sum())}}
    curves = []
    for basis in ("lin", "q4", "k"):
        M.SPLINE = basis
        b = {}
        b["shootings_full"], c = fit_all(full, "n")
        curves.append(c.assign(series="shootings_full", basis=basis))
        b["shootings_window"], c = fit_all(win, "n")
        curves.append(c.assign(series="shootings_window", basis=basis))
        for p in ("trips", "customer", "subscriber"):
            b[f"proxy_{p}"], c = fit_all(win, p)
            curves.append(c.assign(series=p, basis=basis))
            a = M.nb_alpha("n", win)
            w1, c = M.curve_fit(win, "n", a, p)
            b[f"shootings_window_with_{p}"] = {k: (r3(v) if "lo" in v else v) for k, v in w1.items()}
            curves.append(c.assign(series=f"shootings_window_with_{p}", basis=basis))
            if basis == "lin" or p == "trips":
                sh = M.shares(win, "n", p, a, boot=500, seed=1, removed=True)
                b[f"shares_{p}"] = sh
        res[basis] = b
    # registered sensitivity with the primary basis
    M.SPLINE = "lin"
    s = {}
    a = M.nb_alpha("n", win)
    old = M.CONTROLS
    M.CONTROLS = "C(dow) + C(ym) + hol + wet"
    s["year_by_month"] = {"proxy_trips": fit_all(win, "trips")[0], "shootings_full": None,
                          "shares_trips": M.shares(win, "n", "trips", a, boot=300, seed=1, removed=True)}
    fy = full.copy(); fy["ym"] = fy["year"].astype(str) + "-" + fy["month"].astype(str)
    s["year_by_month"]["shootings_full"] = fit_all(fy, "n")[0]
    M.CONTROLS = old
    ws, fs = win[win.month.between(5, 9)], full[full.month.between(5, 9)]
    s["may_sep"] = {"proxy_trips": fit_all(ws, "trips")[0], "shootings_full": fit_all(fs, "n")[0],
                    "shares_trips": M.shares(ws, "n", "trips", M.nb_alpha("n", ws), boot=300, seed=1, removed=True)}
    wl = win.copy(); wl["trips_lag"] = wl["trips"].shift(1); wl = wl.dropna(subset=["trips_lag"])
    s["previous_day_proxy"] = {"shares_trips": M.shares(wl, "n", "trips_lag", a, boot=300, seed=1, removed=True)}
    res["sensitivity_lin"] = s
    # descriptive: linear slope and unadjusted bins
    import statsmodels.formula.api as smf, statsmodels.api as sm
    for y in ("n", "trips"):
        r = smf.glm(f"{y} ~ t5 + {M.CONTROLS}", win, family=sm.families.NegativeBinomial(alpha=M.nb_alpha(y, win, 0.1))).fit(cov_type="HC0")
        res[f"linear_irr_per_5C_{y}_window"] = {"estimate": float(np.exp(r.params["t5"])), "lo": float(np.exp(r.params["t5"] - 1.96 * r.bse["t5"])),
                                                "hi": float(np.exp(r.params["t5"] + 1.96 * r.bse["t5"]))}
    bins = pd.cut(win.TMAX, np.arange(-24, 42, 3))
    win.groupby(bins, observed=True).agg(days=("n", "size"), shootings=("n", "mean"), trips=("trips", "mean"), customer=("customer", "mean"),
                                         subscriber=("subscriber", "mean")).to_csv(OUT / "by_tmax_bin.csv")
    pd.concat(curves).to_csv(OUT / "curves.csv", index=False)
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    (OUT / "sources.json").write_text(json.dumps({"divvy": srcs, "shootings_weather": "data/derived/graph/transfer_chicago/heat_results.json (sources field) and chicago_heat_daily.csv"}, indent=1))
    L = res["lin"]
    pr = lambda v: "%.3f (%.3f to %.3f)" % (v["estimate"], v["lo"], v["hi"])
    print(json.dumps(res["divvy"]))
    for k in ("shootings_full", "shootings_window", "proxy_trips", "proxy_customer", "proxy_subscriber", "shootings_window_with_trips"):
        print(k, {r: pr(L[k][r]) for r in ("rr_21_vs_15", "rr_27_vs_21", "rr_33_vs_27")})
    for p in ("trips", "customer", "subscriber"):
        print("shares", p, {k: pr(v) for k, v in L[f"shares_{p}"].items()})
    for b in ("q4", "k"):
        print(b, {k: pr(res[b][k]["rr_33_vs_27"]) for k in ("shootings_full", "shootings_window", "proxy_trips")}, {k: pr(v) for k, v in res[b]["shares_trips"].items()})
    print(json.dumps(s, default=float)[:3000])


if __name__ == "__main__":
    main()
