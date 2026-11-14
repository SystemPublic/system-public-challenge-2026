"""Figure for repro-mmr-cbd-speed. Run after mmr_cbd_speed.py."""
from __future__ import annotations

import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "reproduction"
FIG = ROOT / "figures" / "reproduction"
FIG.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, AQUA, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e"
MMR = {"FY24": 6.9, "FY25": 6.9, "FY26": 6.5}
FYSPAN = {"FY24": ("2023-07-01", "2024-07-01"), "FY25": ("2024-07-01", "2025-07-01"), "FY26": ("2025-07-01", "2026-07-01")}


def main():
    m = pd.read_csv(DER / "mmr_cbd_speed_monthly.csv")
    fy = pd.read_csv(DER / "mmr_cbd_speed_fy.csv")
    m["t"] = pd.to_datetime(m.month + "-15")
    fig, (a, b) = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    for ax in (a, b):
        ax.set_facecolor("#fcfcfb")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.grid(axis="y", color="#e4e3df", lw=0.8)
        ax.axvline(pd.Timestamp("2025-01-05"), color=MUTED, lw=1, ls=":")
    r1 = m[m.area == "R1"]
    a.plot(r1.t, r1.ratio_mph, color=BLUE, lw=2, marker="o", ms=4, label="R1 monthly (total miles / total hours)")
    a.plot(r1.t, r1.mean_mph, color=AQUA, lw=1.5, label="R2 monthly (mean of trip speeds)")
    for k, (s, e) in FYSPAN.items():
        s, e = pd.Timestamp(s), pd.Timestamp(e)
        a.hlines(MMR[k], s, e, color=INK, lw=2.5, label="MMR stated value" if k == "FY24" else None)
        v = fy[(fy.reading == "R1") & (fy.fy == k)].mph.iloc[0]
        a.hlines(v, s, e, color=ORANGE, lw=2.5, ls="--", label="R1 fiscal-year value" if k == "FY24" else None)
        a.text(s + (e - s) / 2, 8.15, f"{k}: MMR {MMR[k]:.1f}, R1 {v:.2f}", ha="center", fontsize=9, color=INK)
    a.text(pd.Timestamp("2025-01-12"), 5.85, "toll starts 5 Jan 2025", fontsize=8, color=MUTED)
    a.set_ylim(5.55, 8.3)
    a.set_ylabel("mph, yellow taxi, CBD, weekdays 8AM-6PM")
    a.legend(loc="lower left", fontsize=7.5, frameon=False, ncol=4, bbox_to_anchor=(0, -0.01))
    a.set_title("Manhattan CBD taxi speed: MMR Fiscal 2026 values and the trip-record reproduction", fontsize=11, loc="left")
    for area, col, lab in (("R1", BLUE, "CBD (both ends in the 38 CBD zones)"),
                           ("MN_NORTH", AQUA, "Manhattan north of 60th St"),
                           ("REST", ORANGE, "Rest of city (neither end in CBD)")):
        g = m[m.area == area].copy()
        base = g[(g.month >= "2024-01") & (g.month <= "2024-12")]
        base = base.miles.sum() / base.hours.sum()
        b.plot(g.t, 100 * (g.ratio_mph / base - 1), color=col, lw=2, label=lab)
    b.axhline(0, color=MUTED, lw=0.8)
    b.set_ylabel("% change from calendar 2024 mean")
    b.legend(loc="lower left", fontsize=8, frameon=False)
    fig.text(0.01, 0.005, "Data: TLC yellow taxi trip records, Jul 2023 - Jun 2026; 2024-25 checked against NYC Open Data rwwi-khbc, irx2-vgm4.\n"
             "Same filters (F1) and holiday rule in every series.", fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    p = FIG / "repro_mmr_cbd_speed.png"
    fig.savefig(p, dpi=160, facecolor="#fcfcfb")
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)], capture_output=True)
    print(p)


if __name__ == "__main__":
    main()
