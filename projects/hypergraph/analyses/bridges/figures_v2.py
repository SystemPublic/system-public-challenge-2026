"""Figure for bridge-crz-injury-crashes-v2, in the style of figures.py."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from analyses.bridges.common import DER, savefig
from analyses.bridges.figures import BLUE, GREY, INK, VERM, rows_plot


def bridge1_v2():
    r = json.loads((DER / "crz_crashes_v2_results.json").read_text())
    R, cp = r["results"], r["composed"]
    p, pl, C = R["primary"], R["placebo_2024"], R["corrected"]
    rows = [
        ("Composed prediction (registered v2)", cp["median"], cp["lo"], cp["hi"], BLUE, "D"),
        ("Endpoint: zone vs Manhattan north of 60th,\n 2025 vs 2022-24 (primary, B0)", p["pct"], p["lo"], p["hi"], VERM, "s"),
        ("  bias bound B_up", C["B_up"]["pct"], C["B_up"]["lo"], C["B_up"]["hi"], VERM, "^"),
        ("  bias bound B_down", C["B_down"]["pct"], C["B_down"]["lo"], C["B_down"]["hi"], VERM, "v"),
        ("Secondary: zone vs 60th-96th St band", R["secondary_area_60_96"]["pct"], R["secondary_area_60_96"]["lo"], R["secondary_area_60_96"]["hi"], GREY, "s"),
        ("Placebo: false start Jan 2024", pl["pct"], pl["lo"], pl["hi"], GREY, "s"),
    ]
    if isinstance(R.get("stable_class_restriction"), dict):
        s = R["stable_class_restriction"]
        rows.insert(4, ("Secondary: stable-coverage records only", s["pct"], s["lo"], s["hi"], GREY, "s"))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})
    rows_plot(axes[0], rows, 0, "Change in injury crashes in the zone relative to Manhattan north of 60th St (%)")
    zc, zn = p["z_chain"], p["z_null"]
    axes[0].text(0.01, 0.01, f"Primary: z against chain {zc:+.2f}, z against no effect {zn:+.2f}, D = {p['D']:.2f}",
                 transform=axes[0].transAxes, fontsize=7.5, color=INK)
    axes[0].set_title("(a) Composed prediction and endpoint, with geocoding bias bounds", fontsize=10, loc="left")
    m = pd.read_csv(DER / "crz_crashes_v2_monthly.csv", index_col=0, parse_dates=True)
    ax = axes[1]
    for col, c, lab in [("zone", VERM, "Congestion Relief Zone"), ("north", INK, "Manhattan north of 60th St")]:
        s = m[col].loc["2022-01-01":"2026-08-01"]
        base = s.loc["2022-01-01":"2024-12-01"].groupby(s.loc["2022-01-01":"2024-12-01"].index.month).mean()
        idx = 100 * s / base.reindex(s.index.month).values
        ax.plot(idx.index, idx.rolling(3, center=True).mean(), color=c, lw=2, label=lab)
    ax.axvline(pd.Timestamp("2025-01-05"), color=GREY, ls="--", lw=0.8)
    ax.axhline(100, color=GREY, lw=0.6)
    ax.set_ylabel("Injury crashes, % of 2022-24 mean for the calendar month\n(3-month centred mean)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title("(b) Monthly geocoded injury crashes, NYPD h9gi-nx95", fontsize=10, loc="left")
    fig.suptitle("Bridge 1, re-analysis: congestion pricing and injury crashes against Manhattan north of 60th Street. "
                 "Pricing began 5 January 2025 (dashed line).", fontsize=10)
    fig.tight_layout()
    return savefig(fig, "bridge_crz_injury_crashes_v2.png")


if __name__ == "__main__":
    print(bridge1_v2())
