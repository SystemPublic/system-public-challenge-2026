"""Figure for the busway tradeoff section: M14 speed by month against other Manhattan routes; pedestrian-injury
crashes by year on 14th Street and the comparison streets; the north/south crosstown estimates from yellow taxis
(referee's exploratory split) and the held-out FHV test. Writes figures/street_space/busway_tradeoff.png."""
from __future__ import annotations

import json
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.street_space.common import DER, FIG
from analyses.street_space.bus import fetch, complete, TREATED


def main():
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
    df, _ = fetch("2019-07-01", "2020-02-01")
    routes = complete(df, ("2019-07-01", "2019-09-01"), ("2019-10-01", "2020-02-01"))
    ctl = df[df.route_id.isin([r for r in routes if not r.startswith("M14")])].groupby("month")[["mi", "hr"]].sum()
    tr = df[df.route_id.isin(TREATED)].groupby("month")[["mi", "hr"]].sum()
    for s, lab, col in ((tr, "M14A/D SBS", "#c0392b"), (ctl, "other Manhattan routes", "#566573")):
        v = s.mi / s.hr
        ax[0].plot(v.index, v.values, marker="o", color=col, label=lab)
    ax[0].axvline(pd.Timestamp("2019-09-20"), color="#c0392b", ls="--", lw=0.8)
    ax[0].set_ylabel("weekday speed, mph")
    ax[0].set_title("Bus speed (MTA cudb-vcni)", fontsize=9, loc="left")
    ax[0].legend(fontsize=7, frameon=False)
    ax[0].tick_params(axis="x", labelrotation=45, labelsize=7)

    p = json.loads((DER / "peds_final.json").read_text())["yearly"]
    yrs = [str(y) for y in range(2015, 2022)]  # whole calendar years inside the fetched window
    for c, col in (("14th", "#c0392b"), ("23rd", "#2471a3"), ("34th", "#7f8c8d"), ("42nd", "#a6acaf"), ("57th", "#d5d8dc")):
        v = np.array([p[y].get(c, 0) if y in p else 0 for y in yrs], float) if isinstance(p.get("2014"), dict) else np.array([p[c].get(y, 0) for y in yrs], float)
        ax[1].plot([int(y) for y in yrs], 100 * v / v[:4].mean(), marker="o", color=col, label=c, lw=2 if c == "14th" else 1)
    ax[1].axvline(2019.75, color="#c0392b", ls="--", lw=0.8)
    ax[1].set_ylabel("crashes injuring a pedestrian\n(2015-18 mean = 100)")
    ax[1].set_title("Pedestrian-injury crashes, 9th to 3rd Av", fontsize=9, loc="left")
    ax[1].legend(fontsize=7, frameon=False, ncol=2)

    f = json.loads((DER / "fhv_final.json").read_text())
    rows = [("yellow, north\n(referee, exploratory)", 7.4, 2.8, 12.1, "#7f8c8d"),
            ("yellow, south\n(referee, exploratory)", -1.5, -5.5, 2.7, "#7f8c8d"),
            ("FHV, north\n(registered)", f["north_s_lt"]["E_pct"], f["north_s_lt"]["lo_pct"], f["north_s_lt"]["hi_pct"], "#c0392b"),
            ("FHV, south\n(registered)", f["south_s_lt"]["E_pct"], f["south_s_lt"]["lo_pct"], f["south_s_lt"]["hi_pct"], "#c0392b")]
    for i, (lab, e, lo, hi, col) in enumerate(rows[::-1]):
        ax[2].errorbar(e, i, xerr=[[e - lo], [hi - e]], fmt="o", color=col, capsize=3)
    ax[2].set_yticks(range(4), [r[0] for r in rows[::-1]], fontsize=7)
    ax[2].axvline(0, color="black", lw=0.6)
    ax[2].axvline(7, color="#2471a3", lw=1, ls="--")
    ax[2].set_xlabel("% change in crosstown trip duration")
    ax[2].set_title("Crosstown car trips, north and south of 14th", fontsize=9, loc="left")
    fig.text(0.01, 0.01, "Sources: MTA bus speeds (data.ny.gov cudb-vcni); NYPD collisions (h9gi-nx95); TLC yellow and FHV trip records. "
             "analyses/street_space/figures2.py", fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = FIG / "busway_tradeoff.png"
    fig.savefig(out, dpi=150)
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], capture_output=True)


if __name__ == "__main__":
    main()
