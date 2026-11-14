"""Figure for transit-gtrain-substitution: first stage, pickup gap by day, and the registered estimates."""
import json
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyses.transit.gtrain_common import DER, FIG, G_ONLY, PHASES, ROOT, TREATED

SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
BLUE, GREY, INK, MUTED = "#1f6fd0", "#8a8f98", "#1c1e21", "#5f6670"
SHIFT = pd.Timedelta(days=364)


def shade(ax, labels=False):
    for ph, (a, b) in PHASES.items():
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b) + pd.Timedelta(days=1), color="#000000", alpha=0.04 + 0.025 * (ph % 2), lw=0)
        if labels:
            mid = pd.Timestamp(a) + (pd.Timestamp(b) - pd.Timestamp(a)) / 2
            ax.text(mid, 1.02, f"phase {ph}", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8, color=MUTED)


def main():
    res = json.loads((DER / "gtrain_results.json").read_text())
    est = res["estimates"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={"width_ratios": [1, 1, 1.05]})

    # (a) entries at stations coded closed, as a share of their June mean, in the phase they were closed
    s = pd.read_csv(DER / "gtrain_subway_entries.csv", dtype={"station_complex_id": str})
    s["d"] = pd.to_datetime(s["d"])
    ax = axes[0]
    days = pd.date_range("2024-06-01", "2024-09-30")
    for year, col in ((2023, GREY), (2024, BLUE)):
        sy = s[s.d.dt.year == year].copy()
        if year == 2023:
            sy["d"] = sy["d"] + SHIFT
        tot = pd.Series(0.0, index=days)
        for cid, (_, _, phases) in G_ONLY.items():
            if phases:
                tot = tot.add(sy[sy.station_complex_id == cid].set_index("d")["entries"].reindex(days, fill_value=0))
        ax.plot(days, tot / 1000, color=col, lw=1.6)
    shade(ax, True)
    ax.set_ylabel("entries per day at nine G-only stations (thousands)")
    ax.set_title("a. Subway entries, nine G-only stations that closed\n    in one or two phases (blue 2024, grey 2023)", loc="left", fontsize=10, pad=18)
    ax.set_ylim(0)

    # (b) treated minus control mean log pickups, relative to June
    p = pd.read_csv(DER / "gtrain_panel.csv")
    p["d"] = pd.to_datetime(p["dstr"])
    p["ly"] = np.log(p["n"].clip(lower=1))
    ax = axes[1]
    for year, col in ((2023, GREY), (2024, BLUE)):
        q = p[p.year == year]
        t = q[q.zone.isin(TREATED)].groupby("d")["ly"].mean()
        c = q[~q.zone.isin(TREATED)].groupby("d")["ly"].mean()
        gap = (t - c)
        gap = 100 * (gap - gap[:"2024-06-27"].mean())
        ax.plot(gap.index, gap.rolling(7, center=True, min_periods=4).mean(), color=col, lw=1.6)
    ax.axhline(0, color=MUTED, lw=0.6)
    shade(ax, True)
    ax.set_ylabel("treated minus control zones, log points x 100 (June = 0)")
    ax.set_title("b. App pickups, seven treated zones against 32 controls\n    (7-day mean; blue 2024, grey 2023)", loc="left", fontsize=10, pad=18)

    # (c) estimates
    ax = axes[2]
    rows = [("Primary: 7 zones, closed days", "primary", BLUE), ("Placebo: same model, 2023", "placebo_2023", GREY),
            ("G-dependent zones (3)", "g_dependent", BLUE), ("Phase 1", "phase1", BLUE), ("Phase 2", "phase2", BLUE),
            ("Phase 3", "phase3", BLUE), ("Triple difference with 2023", "triple_difference", BLUE),
            ("Poisson counts", "poisson", BLUE), ("All Brooklyn and Queens controls", "controls_all_bk_qn", BLUE),
            ("Controls not touching treated", "controls_drop_adjacent", BLUE), ("Weekdays", "weekdays", BLUE)]
    for i, (lab, k, col) in enumerate(rows):
        e = est[k]
        y = len(rows) - i
        ax.plot([100 * e["lo"], 100 * e["hi"]], [y, y], color=col, lw=2, solid_capstyle="round")
        ax.plot(100 * e["estimate"], y, "o", color=col, ms=6, mec="white", mew=1)
    pq = est["primary"]["permutation_95"]
    ax.axvspan(100 * pq[0], 100 * pq[1], color="#000000", alpha=0.05, lw=0)
    ax.text(100 * pq[0], 0.25, "95% of placebo-in-space draws", fontsize=7.5, color=MUTED, va="bottom")
    ax.axvline(0, color=MUTED, lw=0.6)
    ax.axvline(2, color=MUTED, lw=0.6, ls=":")
    ax.axvline(12, color=MUTED, lw=0.6, ls=":")
    ax.text(7, len(rows) + 0.75, "predicted range", ha="center", fontsize=7.5, color=MUTED)
    ax.set_yticks(range(1, len(rows) + 1))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8.5)
    ax.set_ylim(0.2, len(rows) + 1.2)
    ax.set_xlabel("change in daily pickups while the station was closed, log points x 100")
    ax.set_title("c. Estimates with zone-clustered 95% intervals", loc="left", fontsize=10, pad=18)

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8.5, colors=INK)
        ax.yaxis.label.set_size(8.5)
        ax.xaxis.label.set_size(8.5)
    for ax in axes[:2]:
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b"))
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
        ax.grid(axis="y", color="#000000", alpha=0.07, lw=0.6)
    fig.suptitle("Summer 2024 G train shutdown: entries at closed stations fell 99%; app pickups rose about 4%, not distinguishable from zone-to-zone variation",
                 x=0.01, ha="left", fontsize=11.5, color=INK)
    fig.text(0.01, -0.03, "Sources: TLC High Volume FHV trip records (June to September 2023 and 2024); MTA Subway Hourly Ridership (data.ny.gov wujg-7c2s). "
             "Claim transit-gtrain-substitution, registered before the data were queried.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = FIG / "gtrain_shutdown_pickups.png"
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    subprocess.run(["sips", "--embedProfile", SRGB, str(out)], capture_output=True)
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
