"""One-page summary: each mobility claim's city estimate and interval against its registered prediction range."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyses.mobility.common import ROOT, savefig

# registered ranges, copied from the registrations (claims/registered/mob-*.json); converted to percent where needed
ROWS = [
    ("mob-crz-traffic", "CBD taxi/FHV speed vs rest of city, 2025 (%)", (5, 15), "pct"),
    ("mob-crz-air", "PM2.5 at PS 19 vs other boroughs, 2025 (%)", (-8, 0), "pct"),
    ("mob-crz-air-nyccas", "NYCCAS NO2, UHF 306-310 vs outside Manhattan, 2025 (%)", (-10, -3), "pct"),
    ("mob-asthma-pollution", "Child asthma ED per 10 ppb NO2, poverty-adj. (%); shaded = research (Khreis 2017)", (9.8, 37.5), "ratio"),
    ("mob-speedcam-247", "Injury crashes, new vs old camera hours (%)", (-8, 0), "ratio"),
    ("mob-active-commute-obesity", "Adult obesity per 10 pts walk/bike commute (points)", (-4, -0.5), "pts"),
]


def main():
    fig, axes = plt.subplots(len(ROWS), 1, figsize=(8, 7.5))
    for ax, (cid, label, rng, kind) in zip(axes, ROWS):
        o = json.loads((ROOT / "claims" / "outcomes" / f"{cid}.json").read_text())
        e = o["city_effect"]
        est, lo, hi = e["estimate"], e["lo"], e["hi"]
        if kind == "ratio":
            est, lo, hi = (100 * (v - 1) for v in (est, lo, hi))
        ax.axvspan(*rng, color="#f5d6d2", lw=0, label="registered prediction")
        ax.axvline(0, color="#888", lw=0.7)
        ax.errorbar([est], [0], xerr=[[est - lo], [hi - est]], fmt="o", color="#2c3e50", capsize=3)
        lo_x = min(lo, rng[0], 0)
        hi_x = max(hi, rng[1], 0)
        pad = 0.1 * (hi_x - lo_x)
        ax.set_xlim(lo_x - pad, hi_x + pad)
        ax.set_yticks([])
        ax.set_title(f"{cid}: {o['verdict']}  |  {label}", fontsize=8, loc="left")
        ax.tick_params(axis="x", labelsize=7)
    axes[0].legend(frameon=False, fontsize=7, loc="upper left")
    fig.suptitle("Mobility claims: city estimate with 95% interval (dot) against the registered range (shaded)", fontsize=9)
    fig.tight_layout()
    print(savefig(fig, "mobility_claims_summary.png"))


if __name__ == "__main__":
    main()
