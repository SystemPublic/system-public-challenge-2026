"""Figure for transit-fhv-price-subway. Usage: python -m analyses.transit.fhv_price_subway_figure"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = json.loads((ROOT / "data" / "derived" / "transit" / "fhv_price_subway_results.json").read_text())
FIG = ROOT / "figures" / "transit"
FIG.mkdir(parents=True, exist_ok=True)
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
INK, GREY, BLUE, ORANGE = "#1a1a1a", "#8a8a8a", "#2a6fb0", "#c8641e"


def main():
    fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={"width_ratios": [1, 1.15]})
    wk = pd.DataFrame(RES["weekly_2019"])
    for y, c, lw in (("2017", "#b9b9b9", 1.4), ("2018", GREY, 1.6), ("2019", BLUE, 2.4)):
        s = wk[wk.year == y].sort_values("week")
        a.plot(s.week + 0.5, 100 * s.log_ratio_rel_pre, color=c, lw=lw, marker="o", ms=3.5, label=y)
        a.text(s.week.iloc[-1] + 0.7, 100 * s.log_ratio_rel_pre.iloc[-1], y, color=c, va="center", fontsize=10)
    a.axvline(0, color=INK, lw=0.8, ls=":")
    a.axhline(0, color=INK, lw=0.6)
    a.text(0.1, a.get_ylim()[1], "surcharge begins\n2 Feb 2019", fontsize=8.5, va="top", color=INK)
    a.set_xlabel("weeks from the first Monday of February")
    a.set_ylabel("inside / outside weekday entries,\n% difference from the January mean of the same year")
    a.set_title("(a) Subway entries south of 96th St relative to the rest", loc="left", fontsize=11)
    a.set_xlim(-3.2, 9.2)

    P, S = RES["primary_2019"], RES["secondary_2025"]
    C = {"p_lo": 0.05, "p_c": 0.2, "p_hi": 1.3}  # the range registered before the data were seen
    rows = [("2019 primary (vs same weeks of 2018)", P["primary"], BLUE),
            ("placebo: 2018 vs 2017", P["placebo_2018_vs_2017"], GREY),
            ("control: Manhattan north of 96th", P["S1_control_manhattan_north"], BLUE),
            ("control: Bronx, Brooklyn, Queens", P["S2_control_bronx_brooklyn_queens"], BLUE),
            ("nights 20:00-04:00", P["S7_night_20_to_04"], BLUE),
            ("weekends", P["S8_weekends"], BLUE),
            ("2025 zone toll, secondary (vs 2024)", S["estimate"], ORANGE),
            ("2025 placebo: 2024 vs 2023", S["placebo_2024_vs_2023"], GREY)]
    n = len(rows)
    b.axvspan(C["p_lo"], C["p_hi"], color="#dfe9f3", lw=0)
    b.axvline(C["p_c"], color=BLUE, lw=0.8, ls="--")
    b.axvline(0, color=INK, lw=0.7)
    for i, (lab, r, c) in enumerate(rows):
        yy = n - 1 - i
        b.plot([r["lo"], r["hi"]], [yy, yy], color=c, lw=2)
        b.plot(r["pct"], yy, "o", color=c, ms=6)
        b.text(min(r["hi"], 5.2) + 0.1, yy, f"{r['pct']:+.2f}", va="center", fontsize=8.5, color=c)
    b.set_yticks(range(n))
    b.set_yticklabels([r[0] for r in rows][::-1], fontsize=9)
    b.set_xlabel("relative change in entries inside the charged area, % (95% interval)")
    b.set_title("(b) Estimates; the shaded band is the registered range for 2019 (+0.05% to +1.3%)", loc="left", fontsize=11)
    b.axhline(1.5, color="#cccccc", lw=0.6)
    b.set_xlim(-5.5, 6.2)  # the weekend interval (-17 to +23) runs off both sides
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    p = FIG / "fhv_price_subway.png"
    fig.savefig(p, dpi=160, bbox_inches="tight")
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], capture_output=True)
    print(p.relative_to(ROOT))


if __name__ == "__main__":
    main()
