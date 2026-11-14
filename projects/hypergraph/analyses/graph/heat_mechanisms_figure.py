"""Path diagram and first-link curves for the heat-mechanisms experiment.

Reads data/derived/graph/heat_mechanisms/city_results.json and mediator_curves.csv.
Writes figures/graph/heat_mechanisms_paths.png and heat_mechanisms_curves.png (sRGB tagged).
"""
import json
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "graph" / "heat_mechanisms"
F = ROOT / "figures" / "graph"
INK, GRAPH, CITY, MUTED = "#1a1a1a", "#3b5b92", "#a34a28", "#6b6b6b"


def tag(p):
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(p)],
                   check=False, capture_output=True)


def f3(e):
    return f"{e['estimate']:.2f} ({e['lo']:.2f} to {e['hi']:.2f})"


def pct(r):
    z = lambda v: f"{round(100 * v) + 0:d}"
    return f"{z(r['attenuation'])}% ({z(r['attenuation_lo'])} to {z(r['attenuation_hi'])})"


def box(ax, x, y, w, h, text, face="#f4f1ea"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.012",
                                fc=face, ec=INK, lw=1.0))
    ax.text(x, y, text, ha="center", va="center", fontsize=10.5, color=INK)


def arrow(ax, a, b, style="-", color=INK):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, lw=1.2, color=color, linestyle=style,
                                 shrinkA=0, shrinkB=0))


def paths():
    R = json.loads((D / "city_results.json").read_text())
    fig, ax = plt.subplots(figsize=(15, 10.5), dpi=200)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(0, 1)
    ax.axis("off")
    xl, xm, xr, bw, mw = 0.05, 0.5, 0.95, 0.085, 0.15
    ys = {"direct": 0.90, "noise_street": 0.73, "ems_drug": 0.49, "ems_edp": 0.31, "sleep": 0.13}
    box(ax, xl, 0.52, bw, 0.86, "Daily\nmaximum\ntemperature\n(Central Park)", face="#e9eef5")
    box(ax, xr, 0.52, bw, 0.86, "Shooting\nincidents\nper day\n(NYPD)", face="#f5e9e4")
    L, Rr = xl + bw / 2 + 0.012, xr - bw / 2 - 0.012
    ml, mr = xm - mw / 2 - 0.012, xm + mw / 2 + 0.012
    cl, cr = (L + ml) / 2, (mr + Rr) / 2

    def lab(x, y, g, c):
        ax.text(x, y + 0.012, g, ha="center", va="bottom", fontsize=8.1, color=GRAPH, linespacing=1.25)
        ax.text(x, y - 0.014, c, ha="center", va="top", fontsize=8.6, color=CITY, linespacing=1.25)

    y = ys["direct"]
    arrow(ax, (L, y), (Rr, y))
    lab(0.5, y, "Graph: no finding links temperature to gun violence. Homicide +4.9% to +9.5% per 5 C (2 studies);\n"
        "violent crime +32% on days at or above 25 C (South Africa, 1 study, found by variable name)",
        "NYC: shootings IRR 1.146 (1.130 to 1.163) per 5 C, 2006 to 2026; from 27 to 33 C they rise by a factor of "
        + f3(R["shootings_curve"]["rr_33_vs_27"]))
    rows = [
        ("noise_street", "People outdoors\n311 street noise\ncomplaints",
         "Graph: sign negative. Walking OR 0.95 per 1 C\n(Korea, 1 study); activity r = -0.28 (1 study)",
         "Graph: no finding that people outdoors raise violence;\n14 of 16 findings run from crime to less activity"),
        ("ems_drug", "Intoxication\nEMS drug and alcohol\ndispatches",
         "Graph: no hot-day drinking finding. Substance-use\nED visits IRR 1.08 (1.07 to 1.10), extreme heat days",
         "Graph: alcohol and violence, 72 of 76 positive. NYC 1993-95:\ncocaine-positive share of homicides the same on hot days"),
        ("ems_edp", "Mental health crisis\nEMS psychiatric\ndispatches",
         "Graph: 3 of 3 positive. Mental-health ED visits\nIRR 1.08 (1.07 to 1.09), extreme heat days",
         "Graph: mental disorder and violence, 18 of 20 positive,\nmostly victimisation or traits of persons"),
    ]
    for key, name, g1, g2 in rows:
        y, r = ys[key], R[key]
        box(ax, xm, y, mw, 0.085, name)
        arrow(ax, (L, y), (ml, y))
        arrow(ax, (mr, y), (Rr, y))
        fl = r["first_link"]
        lab(cl, y, g1, f"NYC: IRR {f3(fl['irr_per_5C'])} per 5 C;\n27 to 33 C: factor {f3(fl['rr_33_vs_27'])}")
        lab(cr, y, g2, f"NYC: removes {pct(r['primary'])} of the temperature slope;\n"
            f"{100 * r['s1_year_by_month']['attenuation']:.0f}% with year-by-month terms")
    b, dk = R.get("bike", {}), R.get("drinking311", {})
    if "first_link" in b:
        ax.text(0.5, ys["noise_street"] - 0.105, f"Other outdoor proxies. Bicycle counts: IRR {f3(b['first_link']['irr_per_5C'])} per 5 C, "
                f"27 to 33 C factor {f3(b['first_link']['rr_33_vs_27'])}, removes {pct(b['primary'])}.\n"
                f"311 public drinking complaints: IRR {f3(dk['first_link']['irr_per_5C'])}, removes {pct(dk['primary'])}.",
                ha="center", va="center", fontsize=8.8, color=CITY)
    y = ys["sleep"]
    box(ax, xm, y, mw, 0.085, "Sleep loss\nno daily NYC\nseries", face="#ffffff")
    arrow(ax, (L, y), (ml, y), style=(0, (4, 3)), color=MUTED)
    arrow(ax, (mr, y), (Rr, y), style=(0, (4, 3)), color=MUTED)
    lab(cl, y, "Graph: temperature and sleep quality, 8 findings counted,\nnone returned by the API. Trouble sleeping RR 2.2\n"
        "(1.6 to 3.2) at high indoor temperature (1 study)", "NYC: not tested")
    lab(cr, y, "Graph: poor sleep and aggression r = 0.28 (0.25 to 0.31),\nmeta-analysis; 21 of 24 findings positive", "NYC: not tested")
    ax.text(0.5, 0.035, "Blue: System Public Graph, abstracts read. Brown: New York City daily data, negative binomial models with day of week, "
            "month, year, holiday and rain.\nShares are mediation by proxy with bootstrap 95% intervals, not identified effects.",
            fontsize=8.4, color=MUTED, ha="center", va="center")
    p = F / "heat_mechanisms_paths.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    tag(p)


def curves():
    c = pd.read_csv(D / "mediator_curves.csv")
    names = {"shootings": "Shooting incidents", "noise_street": "311 street noise complaints", "bike": "Bicycle counts",
             "ems_drug": "EMS drug and alcohol dispatches", "ems_edp": "EMS psychiatric dispatches",
             "drinking311": "311 public drinking complaints"}
    cols = {"shootings": INK, "noise_street": "#a34a28", "bike": "#3b5b92", "ems_drug": "#5a8a4a", "ems_edp": "#8a5a9a",
            "drinking311": "#b8902a"}
    fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
    for s, g in c.groupby("series", sort=False):
        ax.plot(g["tmax_c"], g["rr"], color=cols[s], lw=2.4 if s == "shootings" else 1.5, label=names[s])
        ax.fill_between(g["tmax_c"], g["lo"], g["hi"], color=cols[s], alpha=0.10, lw=0)
    ax.axhline(1, color=MUTED, lw=0.7)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4])
    ax.set_yticklabels(["0.25", "0.5", "1", "2", "4"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Daily maximum temperature at Central Park (C)")
    ax.set_ylabel("Rate ratio against a 15 C day (log scale)")
    ax.set_title("Daily series against temperature, within month and year", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    p = F / "heat_mechanisms_curves.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    tag(p)


if __name__ == "__main__":
    paths()
    curves()
