"""Figures for docs/policy_simulation.md: the chain, the held-out test and the scenario intervals.
Run: python -m analyses.simulate.figures
"""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "simulate"
FIG = ROOT / "figures" / "simulate"
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
COL = {"a": "#0072B2", "b": "#009E73", "c": "#8a8a8a", "x": "#D55E00"}


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / name
    fig.savefig(p, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], check=True, capture_output=True)
    print("wrote", p.relative_to(ROOT))


def chain():
    P = json.loads((DER / "parameters.json").read_text())["parameters"]
    rng = lambda k, nd=2: f"{P[k]['lo']:.{nd}f} to {P[k]['hi']:.{nd}f}"
    fig, ax = plt.subplots(figsize=(11.5, 6.3))
    ax.set_xlim(0, 11.5), ax.set_ylim(0, 6.3), ax.axis("off")
    nodes = {"toll": (0.9, 3.9, "Toll by weekday\nand band of hours"), "ent": (3.3, 3.9, "Vehicle entries"),
             "spd": (5.7, 3.9, "Speed in the zone"), "amb": (8.1, 3.9, "Ambulance\ntravel time"),
             "sur": (10.5, 3.9, "Cardiac-arrest\nsurvivors"), "rev": (3.3, 1.9, "Toll revenue"),
             "ret": (5.7, 1.9, "Visits, retail and\nrestaurant activity"), "cra": (4.5, 5.7, "Injury crashes")}
    for k, (x, y, t) in nodes.items():
        ax.add_patch(FancyBboxPatch((x - 0.85, y - 0.38), 1.7, 0.76, boxstyle="round,pad=0.03", fc="#f4f4f4", ec="#444", lw=1))
        ax.text(x, y, t, ha="center", va="center", fontsize=9.5)

    def arrow(a, b, text, typ, dy=0.0, rad=0.0, tx=None, ty=None):
        (x1, y1, _), (x2, y2, _) = nodes[a], nodes[b]
        if y1 == y2:
            p1, p2 = (x1 + 0.88, y1), (x2 - 0.88, y2)
        elif y2 < y1:
            p1, p2 = (x1, y1 - 0.41), (x2, y2 + 0.41)
        else:
            p1, p2 = (x1 + (0.3 if x2 > x1 else -0.3), y1 + 0.41), (x2 + (-0.4 if x2 > x1 else 0.4), y2 - 0.41)
        ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>", color=COL[typ], lw=2.0, connectionstyle=f"arc3,rad={rad}"))
        ax.text(tx if tx is not None else (p1[0] + p2[0]) / 2, ty if ty is not None else (p1[1] + p2[1]) / 2 + dy, text,
                ha="center", va="center", fontsize=7.6, color=COL[typ],
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))

    arrow("toll", "ent", f"[c] {rng('k_toll', 3)}\nof paying entries\nper dollar", "c", dy=0.62)
    arrow("ent", "spd", f"[a] elasticity\n{rng('beta_speed')}\nsign not fixed by the data", "x", dy=0.62)
    arrow("spd", "amb", f"[a] elasticity\n{rng('theta_ems')}\nheld-out slope agrees", "a", dy=0.62)
    arrow("amb", "sur", f"[b] log odds {rng('surv_per_min')}\nper minute\n(other countries)", "b", dy=0.62)
    arrow("ent", "rev", f"[c] revenue per entry\n{rng('charge_factor')} of the car toll", "c", tx=2.15, ty=2.9)
    arrow("ent", "ret", "[c] car share, diversion,\nspending, activity per visit", "c", tx=4.4, ty=2.75)
    arrow("ent", "cra", f"[c] exponent\n{rng('crash_volume', 1)}", "c", tx=2.9, ty=5.0)
    arrow("spd", "cra", f"[c] exponent\n{rng('crash_speed', 1)}", "c", tx=6.1, ty=5.0)
    arrow("spd", "ret", f"[c] visits per 1%\nmore speed, {rng('amenity', 1)}", "c", tx=6.95, ty=2.9)
    ax.text(0.1, 0.75, "[a] estimated in this project from city data     [b] System graph finding, read against its abstract     "
                       "[c] assumption with a wide range", fontsize=8.5, color="#222")
    ax.text(0.1, 0.4, "Orange: the fitted value failed the registered held-out test (sim-crz-holdout-2026), and the range crosses zero. "
                      "Baselines by weekday and band are measured 2025 means.", fontsize=8.5, color=COL["x"])
    ax.set_title("The chain: each arrow is one parameter with an interval and a source", fontsize=11, loc="left")
    save(fig, "chain.png")


def holdout():
    R = json.loads((DER / "holdout_result.json").read_text())["level"]["by_band"]
    bands = ["night", "am", "mid", "pm"]
    lab = ["21:00-05:00", "05:00-10:00", "10:00-16:00", "16:00-21:00"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, keys, title, unit in (
            (axs[0], [("speed_ref", "January-June 2025", "#bbbbbb"), ("speed_pred", "predicted for 2026 from entries", COL["a"]),
                      ("speed_obs", "observed January-June 2026", "#222222")], "Taxi speed in the zone", "mph"),
            (axs[1], [("tt_ref", "January-June 2025", "#bbbbbb"), ("tt_link", "predicted from the observed speed", COL["a"]),
                      ("tt_obs", "observed January-June 2026", "#222222")], "Ambulance travel time, life-threatening calls", "seconds")):
        for i, (k, l, c) in enumerate(keys):
            ax.bar([j + (i - 1) * 0.27 for j in range(4)], [R[b][k] for b in bands], 0.25, label=l, color=c)
        ax.set_xticks(range(4), lab, fontsize=8)
        ax.set_ylabel(unit), ax.set_title(title, fontsize=10, loc="left")
        ax.legend(fontsize=7.5, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Held-out test: links fitted on 2025, weekdays of January-June 2026", fontsize=10.5, x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "holdout_levels.png")


def scenarios():
    S = json.loads((DER / "scenarios.json").read_text())
    names = [n for n in S["scenarios"]]
    outs = [("speed_pct", "Speed, %"), ("revenue_musd", r"Weekday revenue, \$ million a year"), ("ambulance_s", "Ambulance travel time, s"),
            ("arrest_survivors", "Cardiac-arrest survivors a year\n(illustration, not a forecast)"), ("retail_pct", "Retail activity, %")]
    fig, axs = plt.subplots(1, len(outs), figsize=(13, 3.4), sharey=True)
    for ax, (k, t) in zip(axs, outs):
        for i, n in enumerate(names):
            v = S["scenarios"][n]["vs_current"][k]
            ax.plot([v["lo"], v["hi"]], [i, i], color=COL["a"] if not n.endswith("_rn") else COL["b"], lw=3, solid_capstyle="butt")
            ax.plot(v["median"], i, "o", color="#222", ms=4)
        ax.axvline(0, color="#888", lw=0.8)
        ax.set_title(t, fontsize=8.5, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
    axs[0].set_yticks(range(len(names)), [S["scenarios"][n]["label"].replace(" pattern, scaled", ",\nscaled").replace("$", r"\$") for n in names], fontsize=7.5)
    axs[0].invert_yaxis()
    fig.suptitle("Each schedule against the current one: median and 95% interval over 10,000 parameter draws "
                 "(green: scaled to hold revenue).\nOnly revenue separates the schedules; every other interval includes zero.",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "scenarios.png")


if __name__ == "__main__":
    import sys
    for f in ([globals()[a] for a in sys.argv[1:]] or [chain, holdout, scenarios]):
        f()
