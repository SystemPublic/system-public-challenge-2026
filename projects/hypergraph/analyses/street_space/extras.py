"""Secondary and exploratory numbers for the 14th Street busway outcomes (written after the
registered test was run; nothing here decides a verdict).
Writes data/derived/street_space/extras.json and the figures in figures/street_space/."""
from __future__ import annotations

import json
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.street_space.common import DER, FIG, PAIRS, GROUPS, PRE, POST
from analyses.street_space.estimate import load, did, SAMPLES
from analyses.street_space.series import contrast
from analyses.street_space.test import season_E

FILES = [PAIRS / f for f in ("pairs_2016-07_2017-09.csv.gz", "pairs_2017-10_2019-09.csv.gz", "pairs_2019-10_2020-02.csv.gz")]
pct = lambda v: round(float(100 * (np.exp(v) - 1)), 2)


def tag(path):
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(path)],
                   capture_output=True)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    df = load(FILES)
    out = {}
    # 1. Day-bootstrap DiD, Oct-Feb a year apart (secondary).
    out["did_yoy"] = {}
    for s in SAMPLES:
        for v in ("s_lt", "s_ld"):
            r = did(df, s, PRE, POST, var=v)
            out["did_yoy"][f"{s}_{v}"] = r
    # 2. Control-group sensitivity of E (weekday): midtown only, downtown only.
    out["control_sensitivity"] = {}
    for keep in ("c_mid", "c_down"):
        x = df[df.g.isin(["t14", keep])]
        for v in ("s_lt", "s_ld"):
            c, _ = contrast(x, "weekday", v)
            c.index = pd.to_datetime(c.index)
            e, d = season_E(c, 2019)
            pre = d[(d.index >= "2017-07-01") & (d.index <= "2019-09-01")].dropna()
            se = float(pre.std(ddof=1)) * np.sqrt(1 / 5 + 1 / 3)
            out["control_sensitivity"][f"{keep}_{v}"] = {"E_pct": pct(e), "lo_pct": pct(e - 1.96 * se), "hi_pct": pct(e + 1.96 * se)}
    # 3. Levels: mean weekday trip duration and distance for treated pairs, Oct-Feb before and after.
    lv = {}
    for w, (a, b) in {"pre": PRE, "post": POST}.items():
        x = df[(df.d >= a) & (df.d <= b) & SAMPLES["weekday"](df)]
        for g in ("t14", "c_mid", "c_down"):
            y = x[x.g == g]
            lv[f"{g}_{w}"] = {"trips": int(y.n.sum()), "mean_min": round(float(y.s_hr.sum() * 60 / y.n.sum()), 2),
                             "mean_mi": round(float(y.s_mi.sum() / y.n.sum()), 3),
                             "mph": round(float(y.s_mi.sum() / y.s_hr.sum()), 2),
                             "geo_mean_min": round(float(np.exp(y.s_lt.sum() / y.n.sum()) / 60), 2)}
    out["levels_weekday"] = lv
    # 4. Exploratory: weekday trip counts, treated relative to control, Oct-Feb a year apart and the same for summer.
    x = df[SAMPLES["weekday"](df)].copy()
    x["month"] = x.d.dt.to_period("M").dt.to_timestamp()
    cnt = x.groupby(["month", "g"]).n.sum().unstack("g")
    lc = np.log(cnt["t14"]) - np.log(cnt[["c_mid", "c_down"]].sum(axis=1))
    lc.index = pd.to_datetime(lc.index)
    e_cnt, d_cnt = season_E(lc, 2019)
    pl = {t: pct(season_E(lc, t)[0]) for t in (2017, 2018)}
    out["trip_count_E_pct"] = {"2019": pct(e_cnt), "placebo": pl,
                               "sd_monthly_yoy_pct": round(float(d_cnt[(d_cnt.index >= "2017-07-01") & (d_cnt.index <= "2019-09-01")].std() * 100), 2)}
    (DER / "extras.json").write_text(json.dumps(out, indent=1, default=float))

    # Figure 1: monthly year-over-year change of the contrast (weekday), duration and distance.
    fig, axes = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)
    for ax, v, lab, se_key in ((axes[0], "s_lt", "trip duration", "weekday_s_lt"), (axes[1], "s_ld", "metered distance", "weekday_s_ld")):
        c, _ = contrast(df, "weekday", v)
        c.index = pd.to_datetime(c.index)
        _, d = season_E(c, 2019)
        d = 100 * (np.exp(d.dropna()) - 1)
        col = ["#c0392b" if k >= pd.Timestamp("2019-10-01") else "#566573" for k in d.index]
        ax.bar(d.index, d.values, width=25, color=col)
        ax.axhline(0, color="black", lw=0.6)
        ax.axvline(pd.Timestamp("2019-09-20"), color="#c0392b", lw=0.8, ls="--")
        ax.set_ylabel(f"% change, {lab}")
        ax.set_title(f"14th Street pairs minus control pairs, change from a year earlier: {lab}", fontsize=9, loc="left")
    axes[1].text(pd.Timestamp("2019-10-10"), axes[1].get_ylim()[1] * 0.8, "busway\n3 Oct 2019", fontsize=8, color="#c0392b")
    fig.text(0.01, 0.005, "Yellow-taxi trips, weekdays 07:00-18:59. Source: TLC trip records; analyses/street_space/extras.py",
             fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    p = FIG / "busway_yoy_monthly.png"
    fig.savefig(p, dpi=150)
    tag(p)
    plt.close(fig)

    # Figure 2: registered estimate and placebos with intervals.
    t = json.loads((DER / "test_final.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    for ax, k, lab, pred, refute in ((axes[0], "weekday_s_lt", "duration", 5.0, 5.0), (axes[1], "weekday_s_ld", "distance", 1.5, 1.5)):
        ys = ["2017 (placebo)", "2018 (placebo)", "2019 (busway)"]
        for i, yr in enumerate(("2017", "2018", "2019")):
            r = t[k][yr]
            ax.errorbar(r["E_pct"], i, xerr=[[r["E_pct"] - r["lo_pct"]], [r["hi_pct"] - r["E_pct"]]], fmt="o",
                        color="#c0392b" if yr == "2019" else "#566573", capsize=3)
        ax.axvline(0, color="black", lw=0.6)
        ax.axvline(pred, color="#2471a3", lw=1, ls="--")
        ax.text(pred, 2.4, " predicted", color="#2471a3", fontsize=8)
        ax.set_yticks(range(3), ys)
        ax.set_ylim(-0.5, 2.7)
        ax.set_xlabel(f"E, % change in {lab}")
    axes[1].set_yticklabels([])
    fig.text(0.01, 0.01, "E: winter change from a year earlier minus summer change; 95% intervals. Weekdays 07-18.", fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    p = FIG / "busway_registered_estimates.png"
    fig.savefig(p, dpi=150)
    tag(p)
    plt.close(fig)
    print(json.dumps({k: v for k, v in out.items() if k != "did_yoy"}, indent=1))
    for k, r in out["did_yoy"].items():
        print(k, r["did_pct"], r["lo_pct"], r["hi_pct"])


if __name__ == "__main__":
    main()
