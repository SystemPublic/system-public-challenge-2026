"""Figures for the two bridges: link estimates, composed prediction, endpoint observation."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from analyses.bridges.common import DER, savefig

INK, GREY, BLUE, VERM, GREEN = "#222222", "#777777", "#0072B2", "#D55E00", "#009E73"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def rows_plot(ax, rows, null, xlabel):
    """rows: list of (label, est, lo, hi, colour, marker)."""
    n = len(rows)
    for i, (lab, e, lo, hi, col, mk) in enumerate(rows):
        y = n - 1 - i
        ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round")
        ax.plot(e, y, mk, color=col, ms=8, mec="white", mew=1.2)
        ax.text(hi, y + 0.22, f"  {e:+.1f} ({lo:+.1f} to {hi:+.1f})" if null == 0 else f"  {e:.3f} ({lo:.3f} to {hi:.3f})",
                fontsize=7.5, color=INK, va="bottom")
    ax.axvline(null, color=GREY, lw=0.8, ls="--")
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1])
    ax.set_xlabel(xlabel)
    ax.set_ylim(-0.7, n - 0.3)


def bridge1():
    r = json.loads((DER / "crz_crashes_results.json").read_text())
    c = json.loads((DER / "composed_predictions.json").read_text())["bridge-crz-injury-crashes"]
    R = r["results"]
    st, vt, cp = c["speed_term_pct"], c["volume_term_pct"], c["composed_injury_crashes_pct"]
    p, pl = R["primary_injury_crashes"], R["placebo_2024"]
    rows = [
        ("Link: speed +5.7% (mob-crz-traffic)\n x exponent 1.2 (Elvik 2009)", st["median"], st["lo"], st["hi"], GREY, "o"),
        ("Link: volume -7.6% (TLC trips, MTA VMT)\n x elasticity 0.9", vt["median"], vt["lo"], vt["hi"], GREY, "o"),
        ("Composed prediction (registered)", cp["median"], cp["lo"], cp["hi"], BLUE, "D"),
        ("Endpoint: NYPD injury crashes,\n zone vs rest, 2025 vs 2022-24", p["pct"], p["lo"], p["hi"], VERM, "s"),
        ("Placebo: false start Jan 2024", pl["pct"], pl["lo"], pl["hi"], GREY, "s"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), gridspec_kw={"width_ratios": [1.25, 1]})
    rows_plot(axes[0], rows, 0, "Change in injury crashes in the zone relative to the rest of the city (%)")
    axes[0].set_title("(a) Links, composed prediction and endpoint", fontsize=10, loc="left")
    m = pd.read_csv(DER / "crz_crashes_monthly.csv", header=[0, 1], index_col=0, parse_dates=True)
    z = m[("zone", "injury_crashes")]
    rest = m[("city", "injury_crashes")] - z
    ax = axes[1]
    for s, col, lab in [(z, VERM, "Congestion Relief Zone"), (rest, INK, "Rest of city")]:
        s = s.loc["2022-01-01":"2026-08-01"]
        base = s.loc["2022-01-01":"2024-12-01"].groupby(s.loc["2022-01-01":"2024-12-01"].index.month).mean()
        idx = 100 * s / base.reindex(s.index.month).values
        ax.plot(idx.index, idx.rolling(3, center=True).mean(), color=col, lw=2, label=lab)
    ax.axvline(pd.Timestamp("2025-01-05"), color=GREY, ls="--", lw=0.8)
    ax.axhline(100, color=GREY, lw=0.6)
    ax.set_ylabel("Injury crashes, % of 2022-24 mean for the calendar month\n(3-month centred mean)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title("(b) Monthly injury crashes, NYPD h9gi-nx95", fontsize=10, loc="left")
    fig.suptitle("Bridge 1: congestion pricing, speed and injury crashes. Pricing began 5 January 2025 (dashed line).", fontsize=10)
    fig.tight_layout()
    return savefig(fig, "bridge_crz_injury_crashes.png")


def bridge2():
    r = json.loads((DER / "ems_results.json").read_text())["results"]
    c = json.loads((DER / "composed_predictions.json").read_text())["bridge-heat-shootings-ems"]["composed_irr_per5C"]
    e, s = r["endpoint_SHOT_irr_per5C"], r["sensitivity"]
    rows = [
        ("Link: NYPD shooting incidents\n(heat-shootings)", 1.1462, 1.1297, 1.1629, GREY, "o"),
        ("Composed prediction (registered)", c["median"], c["lo"], c["hi"], BLUE, "D"),
        ("Endpoint: FDNY EMS SHOT dispatches", e["estimate"], e["lo"], e["hi"], VERM, "s"),
        ("  same, May-September only", s["warm_season"]["estimate"], s["warm_season"]["lo"], s["warm_season"]["hi"], GREY, "s"),
        ("  same, 2006-2019 only", s["2006_2019"]["estimate"], s["2006_2019"]["lo"], s["2006_2019"]["hi"], GREY, "s"),
        ("Contrast outside the chain:\nEMS STAB dispatches", s["STAB_contrast"]["estimate"], s["STAB_contrast"]["lo"], s["STAB_contrast"]["hi"], GREY, "^"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), gridspec_kw={"width_ratios": [1.25, 1]})
    rows_plot(axes[0], rows, 1, "Rate ratio per 5 C of daily maximum temperature (Central Park)")
    axes[0].set_xlim(1.0, 1.2)
    axes[0].set_title("(a) Links, composed prediction and endpoint", fontsize=10, loc="left")
    ax = axes[1]
    yrs = sorted(int(y) for y in r["annual_SHOT"])
    yrs = [y for y in yrs if y <= 2025]
    ax.plot(yrs, [r["annual_SHOT"][str(y)] for y in yrs], color=VERM, lw=2, marker="s", ms=5, label="EMS SHOT dispatches (76xm-jjuj)")
    ax.plot(yrs, [r["annual_NYPD"][str(y)] for y in yrs], color=INK, lw=2, marker="o", ms=5, label="NYPD shooting incidents (5ucz-vwe8)")
    ax.set_ylim(0, None)
    ax.set_xticks(range(2006, 2026, 3))
    ax.set_ylabel("Per year")
    l2 = r["link_dispatches_per_incident"]
    ax.text(0.02, 0.04, f"Second link: {l2['estimate']:.2f} ({l2['lo']:.2f} to {l2['hi']:.2f}) SHOT dispatches\nper NYPD incident on the same day (OLS, calendar terms)",
            transform=ax.transAxes, fontsize=8, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("(b) The two records, 2006-2025", fontsize=10, loc="left")
    fig.suptitle("Bridge 2: heat, shootings and EMS dispatches for gunshot wounds, 2006 to August 2026", fontsize=10)
    fig.tight_layout()
    return savefig(fig, "bridge_heat_shootings_ems.png")


if __name__ == "__main__":
    print(bridge1())
    print(bridge2())
