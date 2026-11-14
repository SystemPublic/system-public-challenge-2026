"""Figures for docs/street_safety.md from data/derived/street_safety/rlc_did_results.json.
1. Ratio of ratios with 95% intervals, by outcome, with the placebo year and the literature values.
2. Map of camera intersections (old, 2026 expansion) and matched controls."""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data/derived/street_safety"
FIG = ROOT / "figures/street_safety"
FIG.mkdir(parents=True, exist_ok=True)
INK, MUTED, BLUE, ORANGE, SURF = "#0b0b0b", "#52514e", "#2a78d6", "#eb6834", "#fcfcfb"
LABEL = {"rear_end": "Rear-end proxy crashes", "tcd": "'Traffic control disregarded' crashes",
         "injured": "Persons injured or killed", "ped": "Pedestrians injured or killed", "all": "All crashes"}
LIT = {"rear_end": [(1.39, "Høye 2013 +39%"), (0.40, "NYC DOT, rear-end injury -60%")],
       "injured": [(0.71, "Cochrane 2005 RR 0.71")]}


def tag(p):
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)],
                   check=False, capture_output=True)


def forest(d):
    order = ["rear_end", "tcd", "injured", "ped", "all"]
    fig, ax = plt.subplots(figsize=(8.5, 5.0), facecolor=SURF)
    ax.set_facecolor(SURF)
    for i, o in enumerate(order):
        y = len(order) - i
        r = d["results"][o]
        ax.plot([r["lo"], r["hi"]], [y, y], color=BLUE, lw=2, solid_capstyle="round")
        ax.plot(r["rr"], y, "o", color=BLUE, ms=8, mec=SURF, mew=2)
        ax.text(r["hi"] + 0.03, y + 0.12, f"{r['rr']:.2f} ({r['lo']:.2f}-{r['hi']:.2f})", fontsize=8.5, color=INK, va="bottom")
        p = d["placebo_one_year_earlier"][o]
        ax.plot([p["lo"], p["hi"]], [y - 0.28, y - 0.28], color=MUTED, lw=1.2)
        ax.plot(p["rr"], y - 0.28, "o", color=SURF, mec=MUTED, ms=6, mew=1.2)
        for v, lab in LIT.get(o, []):
            ax.plot(v, y + 0.28, marker="D", color=ORANGE, ms=6, mec=SURF, mew=1.5)
            ax.text(v, y + 0.42, lab, fontsize=7.5, color=MUTED, ha="center")
    ax.axvline(1, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.set_yticks(range(len(order), 0, -1), [LABEL[o] for o in order], color=INK, fontsize=9)
    ax.set_xscale("log")
    ax.set_xticks([0.4, 0.6, 0.8, 1, 1.25, 1.6, 2], ["0.4", "0.6", "0.8", "1", "1.25", "1.6", "2"])
    ax.set_xlim(0.35, 2.4)
    ax.set_xlabel("Ratio of ratios: camera intersections against matched controls, after vs before (log scale)", color=MUTED, fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    ax.plot([], [], "o", color=BLUE, label=f"2026 expansion, {d['n_treated']} intersections (95% interval)")
    ax.plot([], [], "o", color=SURF, mec=MUTED, label="Placebo: same sites one year earlier")
    ax.plot([], [], "D", color=ORANGE, label="Published estimates")
    ax.legend(loc="upper center", bbox_to_anchor=(0.3, -0.16), ncol=3, fontsize=8, frameon=False)
    fig.suptitle("Red-light cameras switched on in 2026: crashes at the camera intersections", color=INK, fontsize=11, x=0.02, ha="left")
    fig.tight_layout()
    p = FIG / "rlc_ratio_of_ratios.png"
    fig.savefig(p, dpi=200, facecolor=SURF)
    tag(p)


def site_map(d):
    sd = json.loads((DER / "rlc_sites_geo.json").read_text())
    import sys
    sys.path.insert(0, str(ROOT / "analyses/street_safety"))
    import rlc_did as R
    treated, allc, _ = R.load_sites()
    tset = {(t["lat"], t["lon"]) for t in treated}
    old = [s for s in allc if (s["lat"], s["lon"]) not in tset and s["first"] < "2025-06"]
    fig, ax = plt.subplots(figsize=(7, 7), facecolor=SURF)
    ax.set_facecolor(SURF)
    pool = json.loads((DER / "lpi_gazetteer.json").read_text())["rows"]
    ax.scatter([r["lon"] for r in pool], [r["lat"] for r in pool], s=1, color="#d8d7d2", label="Signalized intersections with LPI (control pool)")
    ax.scatter([s["lon"] for s in old], [s["lat"] for s in old], s=14, color=MUTED, label=f"Cameras before 2025 ({len(old)})")
    ax.scatter([t["lon"] for t in treated], [t["lat"] for t in treated], s=16, color=BLUE, edgecolor=SURF, lw=0.5,
               label=f"Cameras first ticketed Jan-Aug 2026 ({len(treated)})")
    fb = [s for s in sd["sites"] if "FLATBUSH" in s["a"] + s["b"] and s.get("lat")]
    for s in fb:
        ax.annotate("", (s["lon"], s["lat"]))
    ax.set_aspect(1.32)
    ax.axis("off")
    ax.legend(loc="upper left", fontsize=8, frameon=False, markerscale=1.5)
    ax.set_title("Red-light camera intersections, New York City", color=INK, fontsize=11, loc="left")
    fig.tight_layout()
    p = FIG / "rlc_sites_map.png"
    fig.savefig(p, dpi=200, facecolor=SURF)
    tag(p)


if __name__ == "__main__":
    d = json.loads((DER / "rlc_did_results.json").read_text())
    forest(d)
    site_map(d)
    print("ok")


def cohort_series():
    e = json.loads((DER / "exploratory_placebo_adjusted.json").read_text())["feb2026_cohort"]
    q = {}
    for r in e["monthly"]:
        y, m = divmod(r["ym"], 100)
        k = f"{y} Q{(m - 1) // 3 + 1}"
        a = q.setdefault(k, [0, 0, 0, 0])
        a[0] += r["treated_all"]; a[1] += r["control_all_per_site"]; a[2] += r["treated_rear"]; a[3] += r["control_rear_per_site"]
    ks = list(q)[:-1]   # 2026 Q4 holds October only and is left out
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), facecolor=SURF)
    for ax, (i, j, ttl) in zip(axs, [(0, 1, "All crashes"), (2, 3, "Rear-end proxy crashes")]):
        ax.set_facecolor(SURF)
        x = range(len(ks))
        ax.plot(x, [q[k][i] for k in ks], color=BLUE, lw=2, marker="o", ms=5, label=f"{e['n_sites']} camera intersections (Feb 2026)")
        ax.plot(x, [q[k][j] for k in ks], color=MUTED, lw=2, marker="o", ms=5, label="Matched controls, scaled to the same number of sites")
        ax.axvline(ks.index("2026 Q1") + 0.17, color=MUTED, lw=0.8, ls=(0, (3, 3)))
        ax.text(ks.index("2026 Q1") + 0.25, ax.get_ylim()[1] * 0.97, "first tickets", fontsize=8, color=MUTED, va="top")
        ax.set_xticks(list(x)[::2], ks[::2], rotation=45, fontsize=8, color=MUTED)
        ax.set_title(ttl + " per quarter, 2023 Q1 to 2026 Q3", fontsize=10, color=INK, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(colors=MUTED)
    axs[0].legend(fontsize=7.5, frameon=False, loc="lower left")
    fig.tight_layout()
    p = FIG / "rlc_feb_cohort_quarterly.png"
    fig.savefig(p, dpi=200, facecolor=SURF)
    tag(p)


if __name__ == "__main__":
    cohort_series()
