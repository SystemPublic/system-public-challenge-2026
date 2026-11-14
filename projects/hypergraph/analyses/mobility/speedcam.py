"""mob-speedcam-247: 24/7 school-zone speed cameras (from 1 Aug 2022) and injury crashes in the new hours.

New hours = Mon-Fri 22:00-05:59 and all of Sat-Sun; old hours = Mon-Fri 06:00-21:59.
Registered model: Poisson GLM of monthly counts, log E = group + month + group x post, Aug 2021 - Jul 2023,
Pearson-scaled SEs; placebo with a fake start of 1 Aug 2021 on Aug 2020 - Jul 2022.
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from concord import socrata
from analyses.mobility.common import DER, savefig

START = pd.Timestamp("2022-08-01")
SEL = ("date_trunc_ym(crash_date) as m, date_extract_dow(crash_date) as dow, "
       "case(crash_time < '06:00', 'early', crash_time >= '22:00', 'late', true, 'day') as band, "
       "count(*) as crashes, "
       "sum(case(number_of_persons_injured > 0 or number_of_persons_killed > 0, 1, true, 0)) as injury_crashes, "
       "sum(number_of_persons_injured) as injured, sum(number_of_pedestrians_injured) as ped_injured, "
       "sum(number_of_cyclist_injured) as cyc_injured, sum(number_of_persons_killed) as killed")
OUTCOMES = ["injury_crashes", "injured", "ped_injured", "killed", "crashes"]


def load():
    rows, src = socrata.query("h9gi-nx95", select=SEL,
                              where="crash_date >= '2019-01-01T00:00:00' and crash_date < '2025-01-01T00:00:00'",
                              group="m, dow, band", order="m")
    d = pd.DataFrame(rows)
    for c in OUTCOMES:
        d[c] = pd.to_numeric(d[c])
    d["m"] = pd.to_datetime(d["m"])
    d["dow"] = d["dow"].astype(int)  # 0 = Sunday, 6 = Saturday
    d["group"] = np.where(d["dow"].isin([0, 6]) | d["band"].isin(["early", "late"]), "new", "old")
    g = d.groupby(["m", "group"], as_index=False)[OUTCOMES].sum()
    return g, src


def did(g, outcome, start, lo, hi):
    w = g[(g["m"] >= lo) & (g["m"] <= hi)].copy()
    w["post"] = (w["m"] >= start).astype(int)
    w["treat"] = (w["group"] == "new").astype(int)
    w["mm"] = w["m"].dt.strftime("%Y-%m")
    m = smf.glm(f"{outcome} ~ C(mm) + treat + treat:post", data=w, family=sm.families.Poisson()).fit(scale="X2")
    b, se = m.params["treat:post"], m.bse["treat:post"]
    return {"outcome": outcome, "ratio": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)),
            "hi": float(np.exp(b + 1.96 * se)), "p": float(m.pvalues["treat:post"]), "scale": float(m.scale),
            "n": int(m.nobs), "window": [str(lo.date()), str(hi.date())],
            "totals": {f"{k[0]}_post{k[1]}": float(v) for k, v in w.groupby(["group", "post"])[outcome].sum().items()}}


def mechanism():
    """Camera tickets by hour band in July vs September 2022 (Open Parking and Camera Violations)."""
    out = {}
    srcs = []
    for mon in ("07", "09"):
        try:
            rows, src = socrata.query(
                "nc67-uf89",
                select="substring(violation_time, 1, 2) as hh, substring(violation_time, 6, 1) as ap, count(*) as n",
                where=f"violation = 'PHTO SCHOOL ZN SPEED VIOLATION' and issue_date like '{mon}/%/2022'",
                group="hh, ap")
            out[f"2022-{mon}"] = rows
            srcs.append(src)
        except Exception as e:  # noqa: BLE001
            out[f"2022-{mon}"] = f"query failed: {e}"
    return out, srcs


def main():
    g, src = load()
    g.to_csv(DER / "speedcam_monthly_by_group.csv", index=False)
    res = {}
    for o in OUTCOMES:
        res[o] = did(g, o, START, pd.Timestamp("2021-08-01"), pd.Timestamp("2023-07-01"))
        res[o + "_placebo2021"] = did(g, o, pd.Timestamp("2021-08-01"), pd.Timestamp("2020-08-01"), pd.Timestamp("2022-07-01"))
    for k, v in res.items():
        print(f"{k:28s} ratio={v['ratio']:.3f} ({v['lo']:.3f}-{v['hi']:.3f}) p={v['p']:.3g} scale={v['scale']:.1f}")
    mech, msrc = mechanism()
    print(json.dumps(mech)[:1500])
    (DER / "speedcam_results.json").write_text(json.dumps({"results": res, "mechanism": mech, "sources": [src] + msrc},
                                                           indent=1, default=str))

    # event-study style figure: share of injury crashes in new hours, and new/old ratio relative to same month a year earlier
    p = g.pivot(index="m", columns="group", values="injury_crashes")
    share = p["new"] / (p["new"] + p["old"])
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    ax = axes[0]
    ax.plot(p.index, p["old"], color="#2c3e50", label="old hours (Mon-Fri 06:00-21:59)")
    ax.plot(p.index, p["new"], color="#c0392b", label="new hours (nights and weekends)")
    ax.set_ylabel("Crashes with an injury or death, per month")
    ax.set_title("(a) NYPD crashes (h9gi-nx95) by camera-hour group", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax = axes[1]
    ax.plot(share.index, 100 * share, color="#c0392b", marker="o", ms=2.5)
    ax.plot(share.index, 100 * share.rolling(12, center=True).mean(), color="k", lw=1, label="12-month centred mean")
    ax.set_ylabel("Share of injury crashes in new hours (%)")
    ax.set_title("(b) Share in the newly enforced hours", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.axvline(START, color="k", ls="--", lw=0.8)
        ax.axvspan(pd.Timestamp("2020-03-15"), pd.Timestamp("2020-06-30"), color="#ddd", lw=0)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("School-zone speed cameras ran 24/7 from 1 August 2022 (dashed). Grey: spring 2020 lockdown.", fontsize=9)
    fig.tight_layout()
    print(savefig(fig, "speedcam_247_new_vs_old_hours.png"))


if __name__ == "__main__":
    main()
