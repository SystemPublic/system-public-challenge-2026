"""mob-crz-air-nyccas: NYCCAS annual NO2 (and PM2.5) by UHF42, in-zone vs outside Manhattan, 2025 vs 2021-24.

Inference by placebo-in-space (5,000 random sets of 5 comparison UHFs) and placebo-in-time (post = 2024).
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.mobility import ehdp
from analyses.mobility.common import DER, savefig

INZONE = [306, 307, 308, 309, 310]
ADJ = [301, 302, 303, 304, 305]
RNG = np.random.default_rng(20261112)


def did(panel: pd.DataFrame, treated, post_year: int, years) -> float:
    """Two-way FE DiD on a balanced panel = (treated post - treated pre) - (control post - control pre) on logs."""
    p = np.log(panel.loc[:, [y for y in years]])
    pre = [y for y in years if y < post_year]
    post = [y for y in years if y >= post_year]
    ch = p[post].mean(axis=1) - p[pre].mean(axis=1)
    t = ch.index.isin(treated)
    return float(ch[t].mean() - ch[~t].mean())


def analyse(ind, mid, label):
    yrs = [str(y) for y in range(2014, 2026)]
    d = ehdp.measure(ind, mid)
    d = d[d["period"].isin(yrs)]
    w = d.pivot(index="GeoID", columns="period", values="Value")
    w.columns = [int(c) for c in w.columns]
    w.to_csv(DER / f"nyccas_{label}_uhf42_annual.csv", index_label="uhf42")
    main = w.loc[[i for i in w.index if i not in ADJ]]
    years = [2021, 2022, 2023, 2024, 2025]
    est = did(main, INZONE, 2025, years)
    controls = [i for i in main.index if i not in INZONE]
    plac = []
    for _ in range(5000):
        fake = RNG.choice(controls, 5, replace=False)
        sub = main.loc[[i for i in main.index if i not in INZONE]]
        plac.append(did(sub, fake, 2025, years))
    plac = np.array(plac)
    p_one = float((np.sum(plac <= est) + 1) / (len(plac) + 1))
    lo, hi = est - np.percentile(plac, 97.5), est - np.percentile(plac, 2.5)
    time_placebo = did(main, INZONE, 2024, [2021, 2022, 2023, 2024])
    adj = did(w.loc[[i for i in w.index if i not in INZONE]], ADJ, 2025, years)
    pct = lambda v: 100 * (np.exp(v) - 1)
    res = {"label": label, "estimate_log": est, "pct": pct(est), "lo_pct": pct(lo), "hi_pct": pct(hi),
           "p_one_sided_placebo_space": p_one, "placebo_space_pct_2.5_50_97.5": [pct(x) for x in np.percentile(plac, [2.5, 50, 97.5])],
           "placebo_time_2024_pct": pct(time_placebo), "adjacent_301_305_pct": pct(adj),
           "n_uhf": int(len(main)), "group_means": {
               "in-zone": w.loc[INZONE, years].mean().round(2).to_dict(),
               "adjacent": w.loc[ADJ, years].mean().round(2).to_dict(),
               "outside Manhattan": w.loc[controls, years].mean().round(2).to_dict()}}
    print(label, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res.items() if k != "group_means"})
    print(res["group_means"])
    return res, w


def main():
    out = {}
    out["NO2"], wn = analyse(2025, 1431, "NO2")
    out["PM25"], wp = analyse(2023, 1425, "PM25")
    out["sources"] = [ehdp.source(2025, 1431, "NO2 annual mean (ppb), NYCCAS", [str(y) for y in range(2014, 2026)]),
                      ehdp.source(2023, 1425, "PM2.5 annual mean (ug/m3), NYCCAS", [str(y) for y in range(2014, 2026)])]
    (DER / "crz_air_nyccas_results.json").write_text(json.dumps(out, indent=1, default=float))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, w, lab in ((axes[0], wn, "NO2 annual mean (ppb)"), (axes[1], wp, "PM2.5 annual mean (ug/m3)")):
        ctl = [i for i in w.index if i not in INZONE + ADJ]
        for grp, c, nm in ((INZONE, "#c0392b", "in zone (UHF 306-310)"), (ADJ, "#7f8c8d", "Manhattan north of 60th (301-305)"),
                           (ctl, "#2c3e50", "outside Manhattan (32 UHFs)")):
            s = w.loc[grp].mean()
            ax.plot(s.index, s.values, marker="o", ms=3, color=c, label=nm)
        ax.axvline(2024.5, color="k", ls="--", lw=0.8)
        ax.set_ylabel(lab)
        ax.set_xticks(range(2014, 2026, 2))
        ax.legend(frameon=False, fontsize=7)
    axes[0].set_title(f"(a) NO2: DiD 2025 vs 2021-24 = {out['NO2']['pct']:+.1f}% "
                      f"(placebo p = {out['NO2']['p_one_sided_placebo_space']:.2f})", fontsize=9)
    axes[1].set_title(f"(b) PM2.5: DiD = {out['PM25']['pct']:+.1f}% "
                      f"(placebo p = {out['PM25']['p_one_sided_placebo_space']:.2f})", fontsize=9)
    fig.suptitle("NYCCAS annual averages by UHF42 neighbourhood (EHDP). Congestion pricing began January 2025.", fontsize=9)
    fig.tight_layout()
    print(savefig(fig, "crz_air_nyccas_uhf42.png"))


if __name__ == "__main__":
    main()
