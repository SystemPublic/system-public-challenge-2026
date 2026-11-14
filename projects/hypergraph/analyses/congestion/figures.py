"""Figures for docs/congestion_tradeoffs.md. Reads only files in data/derived/congestion/."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.congestion.common import DER, savefig

BLUE, VERM, GREEN, GREY, ORANGE = "#0072B2", "#D55E00", "#009E73", "#777777", "#E69F00"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold"})
TOLL = pd.Timestamp("2025-01-05")


def ems():
    r = json.loads((DER / "ems_results.json").read_text())
    m = pd.read_csv(DER / "ems_monthly_travel.csv", parse_dates=["month"])
    m = m[m.month >= "2022-01-01"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})
    a = ax[0]
    for per, ls in (("peak", "-"), ("overnight", ":")):
        z = m[(m.area == "crz") & (m.period == per)].set_index("month").travel_s
        o = m[(m.area != "crz") & (m.period == per)].assign(t=lambda x: x.travel_s * x.n).groupby("month")[["t", "n"]].sum()
        a.plot(z.index, z.rolling(3, center=True).mean(), ls, color=VERM, label=f"zone, {per} hours")
        a.plot(o.index, (o.t / o.n).rolling(3, center=True).mean(), ls, color=BLUE, label=f"rest of city, {per} hours")
    a.axvline(TOLL, color="k", lw=0.8)
    a.text(TOLL, a.get_ylim()[1], " toll begins", va="top", fontsize=8)
    import matplotlib.dates as mdates
    a.xaxis.set_major_locator(mdates.YearLocator())
    a.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    a.set_ylabel("mean ambulance travel time, seconds\n(3-month centred mean)")
    a.set_title("(a) Travel time rose everywhere")
    a.legend(frameon=False, fontsize=8)
    b = ax[1]
    c = r["composed"]["ratio_lo_median_hi"]
    rows = [("REGISTERED: peak hours, to Aug 2025", r["ems.all.travel.all_outside"]["peak"]["primary_jan_aug_2025"], VERM),
            ("peak hours, to Sep 2026", r["ems.all.travel.all_outside"]["peak"]["full_to_sep_2026"], GREY),
            ("overnight hours, to Aug 2025", r["ems.all.travel.all_outside"]["overnight"]["primary_jan_aug_2025"], GREY),
            ("overnight hours, to Sep 2026", r["ems.all.travel.all_outside"]["overnight"]["full_to_sep_2026"], GREY),
            ("peak, life-threatening calls", r["ems.life_threatening.travel.all_outside"]["peak"]["primary_jan_aug_2025"], GREY),
            ("  same, 2024 placebo", r["ems.life_threatening.travel.all_outside"]["peak"]["placebo_2024"], "#bbbbbb"),
            ("peak, 2024 placebo (all calls)", r["ems.all.travel.all_outside"]["peak"]["placebo_2024"], "#bbbbbb"),
            ("fire units, peak, to Aug 2025", r["fire.all.travel.all_outside"]["peak"]["primary_jan_aug_2025"], GREY)]
    y = np.arange(len(rows))[::-1]
    b.axvspan(100 * (c[0] - 1), 100 * (c[2] - 1), color=GREEN, alpha=0.18, lw=0)
    b.axvline(100 * (c[1] - 1), color=GREEN, lw=1)
    b.axvline(-5.44, color=ORANGE, lw=1.2, ls="--")
    b.axvline(0, color="k", lw=0.6)
    for yi, (lab, e, col) in zip(y, rows):
        b.plot([e["lo"], e["hi"]], [yi, yi], color=col, lw=2)
        b.plot(e["pct"], yi, "o", color=col, ms=6 if col == VERM else 4)
    b.set_yticks(y)
    b.set_yticklabels([x[0] for x in rows], fontsize=8)
    b.set_xlabel("change in zone travel time relative to rest of city, %")
    b.text(-5.44, len(rows) - 0.4, "in proportion\nto speed", color=ORANGE, fontsize=7.5, ha="center")
    b.text(100 * (c[1] - 1), len(rows) - 0.4, "composed\nprediction", color=GREEN, fontsize=7.5, ha="center")
    b.set_ylim(-0.6, len(rows) + 0.3)
    b.set_title("(b) Difference-in-differences estimates, 95% intervals")
    fig.tight_layout()
    print(savefig(fig, "ems_travel_time.png"))


def business():
    v = pd.read_csv(DER / "vacancy_rates.csv")
    r = json.loads((DER / "vacancy_results.json").read_text())
    x = json.loads((DER / "explore_results.json").read_text())
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
    a = ax[0]
    names = {"crz": ("zone (south of 60th St)", VERM), "north": ("Manhattan 60th-110th St", BLUE), "bklic": ("downtown Brooklyn, LIC", GREEN), "rest": ("rest of city", GREY)}
    for k, (lab, col) in names.items():
        s = v[v.area == k]
        a.plot(s.year, 100 * s["mean"], "o-", color=col, label=lab, ms=3.5)
    a.axvline(2024.02, color="k", lw=0.8)
    a.set_ylabel("storefronts vacant on 31 December, %")
    a.set_title("(a) Storefront vacancy")
    a.legend(frameon=False, fontsize=7.5)
    b = ax[1]
    pl = r["placebo_did"] + [r["did_2025"]]
    for e in pl:
        col = VERM if e["year"] == 2025 else GREY
        b.plot([e["year"], e["year"]], [e["lo"], e["hi"]], color=col, lw=2)
        b.plot(e["year"], e["did_points"], "o", color=col)
    b.axhline(0, color="k", lw=0.6)
    b.axhline(1.2, color=ORANGE, ls="--", lw=1)
    b.text(2020.1, 1.3, "rise the test was built to detect", color=ORANGE, fontsize=7.5)
    b.set_ylabel("year-on-year change, zone minus outside, points")
    b.set_title("(b) Registered test: 2025 in red")
    c = ax[2]
    ro = x["restaurant_openings_surviving"]["zone_share_pct"]
    yrs = sorted(ro)
    c.bar([int(y) for y in yrs], [ro[y] for y in yrs], color=[GREY, GREY, VERM, VERM], width=0.6)
    for y in yrs:
        c.text(int(y), ro[y] + 0.4, f"{ro[y]:.0f}%", ha="center", fontsize=8)
    c.set_xticks([int(y) for y in yrs])
    c.set_xticklabels(["2023", "2024", "2025", "2026\n(to Nov)"])
    c.set_ylabel("zone's share of the city's new restaurants, %")
    c.set_title("(c) New restaurants still open (exploratory)")
    fig.tight_layout()
    print(savefig(fig, "business.png"))


def timing():
    g = pd.read_csv(DER / "crz_entries_dow_hour.csv", index_col=0)[["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
    t = pd.read_csv(DER / "taxi_speed_did_day_block.csv")
    bh = pd.read_csv(DER / "bus_speed_did_by_hour.csv")
    fig, ax = plt.subplots(1, 3, figsize=(12.5, 4.2), gridspec_kw={"width_ratios": [1, 1, 1.1]})
    a = ax[0]
    im = a.imshow(g.values / 1000, aspect="auto", cmap="Blues", origin="upper")
    a.set_xticks(range(7)); a.set_xticklabels(g.columns)
    a.set_yticks(range(0, 24, 3)); a.set_yticklabels([f"{h:02d}:00" for h in range(0, 24, 3)])
    for d in range(7):
        s, e_ = (5, 21) if d < 5 else (9, 21)
        a.plot([d - 0.5, d + 0.5, d + 0.5, d - 0.5, d - 0.5], [s - 0.5, s - 0.5, e_ - 0.5, e_ - 0.5, s - 0.5], color=VERM, lw=1)
    plt.colorbar(im, ax=a, label="vehicle entries per hour, thousands", fraction=0.046)
    a.set_title("(a) Entries to the zone, Jan 2025-Oct 2026\n(red outline: peak toll hours)")
    b = ax[1]
    piv = t.pivot(index="hours", columns="day", values="did_vs_north_pct").loc[["05-09", "10-15", "16-20", "21-04"], ["Mon", "Tue-Thu", "Fri", "Sat", "Sun"]]
    im = b.imshow(piv.values, aspect="auto", cmap="RdBu", vmin=-4, vmax=4)
    b.set_xticks(range(5)); b.set_xticklabels(piv.columns)
    b.set_yticks(range(4)); b.set_yticklabels(piv.index)
    for i in range(4):
        for j in range(5):
            b.text(j, i, f"{piv.values[i, j]:+.1f}", ha="center", va="center", fontsize=8.5)
    b.set_title("(b) Taxi speed in the zone after the toll,\nrelative to Manhattan north of 60th St, %")
    c = ax[2]
    for day, col in (("Weekday", BLUE), ("Weekend", VERM)):
        s = bh[bh.day == day]
        c.fill_between(s.hh, s.lo, s.hi, color=col, alpha=0.15, lw=0)
        c.plot(s.hh, s.pct, color=col, label=day.lower())
    c.axhline(0, color="k", lw=0.6)
    c.set_xticks(range(0, 24, 3))
    c.set_xlabel("hour of day")
    c.set_ylabel("bus speed, zone routes relative to other routes, %")
    c.set_title("(c) Bus speed after the toll, by hour")
    c.legend(frameon=False)
    fig.tight_layout()
    print(savefig(fig, "timing.png"))


def hot():
    x = json.loads((DER / "explore_results.json").read_text())["hot_nights"]
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
    a = ax[0]
    h = x["zone_travel_s_by_hour_2023_24"]
    hrs = list(range(24))
    a.bar(hrs, [h[str(i)] for i in hrs], color=[BLUE if (i >= 21 or i < 5) else "#bbbbbb" for i in hrs])
    a.axhline(x["zone_travel_s_min_hour"], color="k", lw=0.7, ls=":")
    a.set_xlabel("hour of day")
    a.set_ylabel("mean ambulance travel time in the zone, s")
    a.set_ylim(300, 700)
    a.set_title("(a) Night hours (blue) are near the quietest hour, 2023-24")
    b = ax[1]
    labs = [("zone_travel", "zone\ntravel"), ("outside_travel", "rest of city\ntravel"), ("zone_response", "zone\nresponse"), ("outside_response", "rest of city\nresponse")]
    for i, (k, lab) in enumerate(labs):
        e = x[f"{k}_hot_vs_other_pct"]
        b.plot([i, i], [e["lo"], e["hi"]], color=VERM if "zone" in k else BLUE, lw=2)
        b.plot(i, e["pct"], "o", color=VERM if "zone" in k else BLUE)
    b.axhline(0, color="k", lw=0.6)
    b.set_xticks(range(4)); b.set_xticklabels([l for _, l in labs])
    b.set_ylabel("nights after a 32 C day against other summer nights, %")
    b.set_title("(b) Overnight EMS times on hot nights (exploratory)")
    fig.tight_layout()
    print(savefig(fig, "hot_nights.png"))


if __name__ == "__main__":
    import sys
    for f in (sys.argv[1:] or ["ems", "business", "timing", "hot"]):
        {"ems": ems, "business": business, "timing": timing, "hot": hot}[f]()
