"""Figures for docs/turn_restrictions.md. Reads data/derived/turn_restrictions/{sites,did_results,
bus_speeds_compare}.json; writes figures/turn_restrictions/*.png with an embedded sRGB profile."""
import json, subprocess
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/derived/turn_restrictions"
F = ROOT / "figures/turn_restrictions"
F.mkdir(parents=True, exist_ok=True)
ICC = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"


def save(fig, name):
    p = F / name
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    subprocess.run(["sips", "--embedProfile", ICC, str(p)], capture_output=True)


def sites_map():
    s = json.loads((D / "sites.json").read_text())["sites"]
    fig, ax = plt.subplots(figsize=(6, 6.5))
    yrs = [int(x["date"][:4]) for x in s]
    sc = ax.scatter([x["lon"] for x in s], [x["lat"] for x in s], c=yrs, s=6, cmap="viridis")
    fig.colorbar(sc, ax=ax, label="Install year", shrink=0.7)
    ax.set_aspect(1 / 0.758)
    ax.set_title(f"Left-turn traffic calming, {len(s)} intersections (NYC DOT, sm2x-35i7)", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    save(fig, "sites_map.png")


def event_plot():
    r = json.loads((D / "did_results.json").read_text())
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True)
    names = {"ped": "Pedestrians injured or killed, within 40 m", "lt": "Crashes with a left-turning vehicle, within 40 m",
             "ped_ring": "Pedestrians injured or killed, 50-200 m ring", "lt_ring": "Left-turn crashes, 50-200 m ring"}
    for ax, o in zip(axes.flat, ["ped", "lt", "ped_ring", "lt_ring"]):
        ev = r["event"][o]
        binof = lambda e: (e + 24) // 3 if e < 0 else 8 + (e - 1) // 3
        qs = list(range(16))
        T = {q: 0 for q in qs}; C = {q: 0 for q in qs}
        for e, (t, c) in ev.items():
            e = int(e)
            if e == 0:
                continue
            T[binof(e)] += t; C[binof(e)] += c
        x = [q * 3 - 23 if q < 8 else (q - 8) * 3 + 2 for q in qs]
        ax.plot(x, [T[q] for q in qs], "-o", ms=3, label="Treated sites")
        ax.plot(x, [C[q] for q in qs], "-o", ms=3, label="Later-treated sites, scaled")
        ax.axvline(0, color="grey", lw=0.8)
        p = r["primary"][o]
        ax.set_title(f"{names[o]}\nratio of ratios {p['ror']:.2f} ({p['lo']:.2f}-{p['hi']:.2f})", fontsize=9)
        ax.set_ylim(bottom=0)
    for ax in axes[1]:
        ax.set_xlabel("Months from installation (3-month bins)")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Left-turn calming: counts by event time, stacked cohorts 2016Q3-2023Q2", fontsize=10)
    fig.tight_layout()
    save(fig, "event_time.png")


def forest():
    r = json.loads((D / "did_results.json").read_text())
    rows = [("ped", "primary"), ("ped_r30", "checks"), ("ped_avoid2020", "checks"),
            ("lt", "primary"), ("lt_r30", "checks"), ("lt_avoid2020", "checks"),
            ("ped_ring", "primary"), ("ped_ring_avoid2020", "checks"), ("lt_ring", "primary"), ("lt_ring_avoid2020", "checks")]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for i, (k, g) in enumerate(rows):
        p = r[g][k]
        y = len(rows) - i
        ax.errorbar(p["ror"], y, xerr=[[p["ror"] - p["lo"]], [p["hi"] - p["ror"]]], fmt="o" if g == "primary" else "s",
                    color="black" if g == "primary" else "grey", capsize=3)
    ax.set_yticks(range(len(rows), 0, -1)); ax.set_yticklabels([k for k, _ in rows], fontsize=8)
    ax.axvline(1, color="grey", lw=0.8)
    ax.set_xlabel("Ratio of ratios (treated vs later-treated), 95% interval")
    ax.set_title("Registered estimates (black) and non-deciding checks (grey)", fontsize=10)
    save(fig, "forest.png")


def bus():
    b = json.loads((D / "bus_speeds_compare.json").read_text())
    ms = sorted(b["monthly_m42"])
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(range(len(ms)), [b["monthly_m42"][m] for m in ms], "-o", ms=3, label="M42 (42nd St)")
    ax.plot(range(len(ms)), [b["monthly_comparison_mean"][m] for m in ms], "-o", ms=3, label="Mean of 6 other crosstown routes")
    ax.set_xticks(range(0, len(ms), 3)); ax.set_xticklabels(ms[::3], rotation=45, fontsize=7)
    ax.set_ylabel("Weekday average speed (mph)")
    ax.set_title("EXPLORATORY: crosstown bus speeds, MTA cudb-vcni", fontsize=10)
    ax.legend(fontsize=8)
    save(fig, "bus_speeds.png")


if __name__ == "__main__":
    sites_map(); event_plot(); forest(); bus()
