"""Can the registered test fail? A simulation on the Chicago design (Midway TMAX and the
calendar; the shootings column is not read). Run BEFORE registration.

Shootings are simulated with the New York shape (rise 1.30 from 15 to 21 C, 1.12 from 27 to
33 C) or with no rise above 27 C. The basis is the registered one (model.SPLINE). The proxy is simulated with the New York bicycle shape
(rise 1.24 from 15 to 21 C, flat above 27 C) or with a continued rise, and with day-to-day
noise of sd 0.25 on the log scale. In the 'chain' scenario 45% of the 15-21 C rise in
shootings passes through the proxy; in the 'none' scenario none does.
Writes data/derived/round2/hot_end/power.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyses.round2.hot_end import model as M

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "derived" / "round2" / "hot_end"
OUT.mkdir(parents=True, exist_ok=True)
d0 = pd.read_csv(ROOT / "data/derived/graph/transfer_chicago/chicago_heat_daily.csv", index_col=0, parse_dates=True,
                 usecols=["date", "TMAX", "PRCP", "dow", "month", "year", "hol", "wet", "t5"]).dropna(subset=["TMAX"])
rng = np.random.default_rng(7)
MEAN, ALPHA = 6.7, 0.03


def pw(t, s_mild, s_hot):
    """piecewise-linear log curve: slope s_mild per 6 C below 27, s_hot per 6 C above."""
    return np.where(t <= 27, s_mild * (t - 27) / 6, s_hot * (t - 27) / 6)


def nb(mu):
    return rng.negative_binomial(1 / ALPHA, 1 / (1 + ALPHA * mu))


def sim(d, proxy_hot, shoot_hot, chain):
    t = d["TMAX"].values
    e = np.zeros(len(d))
    z = rng.normal(0, 0.25 * np.sqrt(1 - 0.5 ** 2), len(d))
    for i in range(1, len(d)):
        e[i] = 0.5 * e[i - 1] + z[i]
    logm = np.log(8000) + pw(t, np.log(1.24), np.log(proxy_hot)) + e - 0.3 * d["wet"].values
    beta = 0.45 * np.log(1.30) / np.log(1.24) if chain else 0.0
    direct = pw(t, np.log(1.30) - beta * np.log(1.24), np.log(shoot_hot) - beta * np.log(proxy_hot))
    mu = MEAN * np.exp(direct + beta * (logm - np.log(8000)) - 0.9 * 0.25)
    d = d.copy()
    d["m"] = np.exp(logm).round()
    d["n"] = nb(mu)
    return d


def run(d, nsim, **kw):
    rows = []
    for _ in range(nsim):
        s = sim(d, **kw)
        c0, _ = M.curve_fit(s, "n", ALPHA)
        c1, _ = M.curve_fit(s, "n", ALPHA, "m")
        cp, _ = M.curve_fit(s, "m", 0.06)
        rows.append({"sh_hot": c0["rr_33_vs_27"]["log"], "sh_hot_se": c0["rr_33_vs_27"]["se"],
                     "px_hot": cp["rr_33_vs_27"]["log"], "px_hot_se": cp["rr_33_vs_27"]["se"],
                     "share_mild": 1 - c1["rr_21_vs_15"]["log"] / c0["rr_21_vs_15"]["log"],
                     "share_hot": 1 - c1["rr_33_vs_27"]["log"] / c0["rr_33_vs_27"]["log"],
                     "rem_hot": c0["rr_33_vs_27"]["log"] - c1["rr_33_vs_27"]["log"]})
    return pd.DataFrame(rows)


full = d0
win = d0.loc["2013-06-27":"2019-12-31"]
res = {"n_days_full": len(full), "n_days_divvy_window": len(win),
       "days_tmax_ge_30_full": int((full.TMAX >= 30).sum()), "days_tmax_ge_30_window": int((win.TMAX >= 30).sum()),
       "days_tmax_ge_33_full": int((full.TMAX >= 33).sum()), "days_tmax_ge_33_window": int((win.TMAX >= 33).sum())}
N = 120
for name, d in (("full", full), ("window", win)):
    for label, kw in (("ny_shape_chain", dict(proxy_hot=0.98, shoot_hot=1.12, chain=True)),
                      ("ny_shape_none", dict(proxy_hot=0.98, shoot_hot=1.12, chain=False)),
                      ("shoot_flat_proxy_rising", dict(proxy_hot=1.12, shoot_hot=1.00, chain=False))):
        if name == "full" and label == "ny_shape_chain":
            continue
        r = run(d, N, **kw)
        a_sh = float(((r.sh_hot - 1.96 * r.sh_hot_se) > 0).mean())
        a_px = float(((r.px_hot + 1.96 * r.px_hot_se) < np.log(1.06)).mean())
        sm_, ss = r.share_mild, r.share_mild.std()
        hm, hs = r.share_hot, r.share_hot.std()
        rh, rs = r.rem_hot, r.rem_hot.std()
        b_sup = float(((sm_ >= 0.20) & (sm_ - 1.96 * ss > 0.10) & (rh < 0.028) & (rh + 1.96 * rs < 0.057)).mean())
        b_ref = float(((sm_ < 0.10) & (sm_ + 1.96 * ss < 0.20)).mean())
        res[f"{name}:{label}"] = {
            "se_log_shootings_33_vs_27": float(r.sh_hot_se.mean()), "se_log_proxy_33_vs_27": float(r.px_hot_se.mean()),
            "mde_shootings_33_vs_27_80pct": float(np.exp(2.8 * r.sh_hot_se.mean())),
            "p_shootings_lower_limit_above_1": a_sh, "p_proxy_upper_limit_below_1.06": a_px,
            "share_mild_mean_sd": [float(sm_.mean()), float(ss)], "share_hot_median_sd": [float(hm.median()), float(hs)],
            "removed_hot_log_mean_sd": [float(rh.mean()), float(rs)],
            "p_b_support": b_sup, "p_b_refute": b_ref}
        print(name, label, json.dumps(res[f"{name}:{label}"], default=float))
(OUT / "power.json").write_text(json.dumps(res, indent=1))
print({k: v for k, v in res.items() if not isinstance(v, dict)})
