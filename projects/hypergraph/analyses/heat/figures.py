"""Figures for the heat topic, from the derived results.

figures/heat/heat_shootings_curve.png   exposure-response, NYC vs literature, with a forest panel per 5 C
figures/heat/heat_ed_curve.png          heat-syndrome ED visits vs TMAX
figures/heat/heat_bridge_chain.png      trees -> temperature -> heat ED, each link's estimate and interval
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analyses.heat.common import DER, FIG, tag_srgb  # noqa: E402

BLUE, ORANGE, AQUA, GREY, INK, INK2 = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GREY, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
                     "savefig.facecolor": "#fcfcfb"})


def per5(pct10_est, lo, hi):
    """Convert a percent change per 10 C to an IRR per 5 C."""
    return tuple(float(np.sqrt(1 + v / 100)) for v in (pct10_est, lo, hi))


def shootings():
    r = json.loads((DER / "shootings_results.json").read_text())
    c = pd.read_csv(DER / "shootings_curve.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1.15, 1]})
    a.fill_between(c["tmax_c"], c["lo"], c["hi"], color=BLUE, alpha=0.18, lw=0)
    a.plot(c["tmax_c"], c["rr"], color=BLUE, lw=2, label="NYC 2006-2026, spline (4 df)")
    med = r["curve"]["median_tmax_c"]
    p = r["primary"]
    a.plot(c["tmax_c"], p["estimate"] ** ((c["tmax_c"] - med) / 5), color=BLUE, lw=1, ls="--",
           label=f"NYC log-linear, IRR {p['estimate']:.3f} per 5 C")
    p84 = r["curve"]["p84_tmax_c"]
    a.errorbar([p84], [1.17], yerr=[[0.05], [0.04]], fmt="o", ms=7, color=ORANGE, capsize=3,
               label="Lyons 2022, 100 cities: RR 1.17 at 84th pct vs median")
    for nm, (e, lo, hi), ls in [("Reeping 2020, Chicago weekdays", per5(34.0, 28.1, 40.2), ":"),
                                ("Xu 2020, NYC homicide", (1.088, 1.015, 1.166), "-.")]:
        a.plot(c["tmax_c"], e ** ((c["tmax_c"] - med) / 5), color=ORANGE, lw=1.2, ls=ls, label=f"{nm} (slope drawn from median)")
    a.axhline(1, color=GREY, lw=0.8)
    a.axvline(med, color=GREY, lw=0.6, ls=":")
    a.set_xlabel("Daily maximum temperature, Central Park (C)")
    a.set_ylabel("Rate ratio of shooting incidents vs median day")
    a.set_title("Shootings by daily maximum temperature", loc="left", color=INK, fontsize=10)
    a.legend(frameon=False, fontsize=7, loc="upper left")
    # forest
    rows = [("NYC primary (lag 0)", p, BLUE)]
    s = r["sensitivity"]
    for k, lab in [("lag01", "NYC lag 0-1"), ("tmin", "NYC using TMIN"), ("warm_season", "NYC May-Sep"),
                   ("2006_2019", "NYC 2006-2019"), ("2020_on", "NYC 2020-2026"), ("murder_incidents_2006_2024", "NYC murders 2006-2024")]:
        rows.append((lab, s[k], BLUE))
    lit = [("Reeping 2020 Chicago, weekdays", per5(34.0, 28.1, 40.2)), ("Reeping 2020 Chicago, weekends", per5(41.6, 34.7, 48.9)),
           ("Xu 2020 NYC homicide (mean T)", (1.088, 1.015, 1.166)), ("Xu 2020 Chicago homicide", (1.095, 1.043, 1.150)),
           ("Rahman 2023 California homicide", (1.049, 1.016, 1.081))]
    for lab, (e, lo, hi) in lit:
        rows.append((lab, {"estimate": e, "lo": lo, "hi": hi}, ORANGE))
    rows.append(("Graph, Xu 2020 as stored (OR 0.095)", {"estimate": 0.095, "lo": 0.043, "hi": 0.15}, AQUA))
    rows.append(("Graph, Rahman 2023 as stored (OR 4.9)", {"estimate": 4.9, "lo": 1.6, "hi": 8.1}, AQUA))
    y = np.arange(len(rows))[::-1]
    for yi, (lab, v, col) in zip(y, rows):
        e = v["estimate"]
        if e < 0.9 or e > 1.5:
            b.annotate(f"{e:g}, off scale" + (" (<)" if e < 1 else " (>)"), (0.97 if e < 1 else 1.27, yi), color=col, fontsize=7,
                       va="center", ha="left" if e < 1 else "right")
            continue
        b.errorbar([e], [yi], xerr=[[e - v["lo"]], [v["hi"] - e]], fmt="o", color=col, ms=5, capsize=2, lw=1.2)
    b.set_yticks(y)
    b.set_yticklabels([r_[0] for r_ in rows], fontsize=7)
    b.axvline(1, color=GREY, lw=0.8)
    b.set_xlim(0.97, 1.28)
    b.set_xlabel("Rate or odds ratio per 5 C (95% CI)")
    b.set_title("Ratio per 5 C: NYC, literature, graph", loc="left", color=INK, fontsize=10)
    b.set_ylim(-0.8, len(rows) - 0.4)
    fig.text(0.01, 0.005, "Sources: NYPD Shooting Incident Data 5ucz-vwe8; NOAA GHCN-Daily USW00094728; papers as cited in docs/heat.md. "
             "Blue NYC, orange literature, green graph as stored.\nReeping converted from % per 10 C; the graph values are percentages mis-read as ratios.", fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    f = FIG / "heat_shootings_curve.png"
    fig.savefig(f, dpi=200)
    plt.close(fig)
    tag_srgb(f)
    return f


def ed():
    r = json.loads((DER / "ed_results.json").read_text())
    c = pd.read_csv(DER / "ed_curve.csv")
    fig, a = plt.subplots(figsize=(5.5, 3.8))
    a.fill_between(c["tmax_c"], c["lo"], c["hi"], color=BLUE, alpha=0.18, lw=0)
    a.plot(c["tmax_c"], c["rr"], color=BLUE, lw=2, label="NYC syndromic heat ED visits, May-Sep 2017-2026")
    p95 = r["curve"]["p95_tmax_c"]
    a.errorbar([p95], [1.663], yerr=[[0.061], [0.064]], fmt="o", color=ORANGE, ms=6, capsize=3,
               label="Sun 2021, US adults: RR 1.66, local 95th pct vs cooler reference")
    a.set_yscale("log")
    a.axhline(1, color=GREY, lw=0.8)
    a.set_xlabel("Daily maximum temperature, Central Park (C)")
    a.set_ylabel("Rate ratio vs warm-season median (log scale)")
    a.set_title("Heat-related ED visits by daily maximum temperature", loc="left", color=INK, fontsize=10)
    a.legend(frameon=False, fontsize=7, loc="upper left")
    fig.text(0.01, 0.005, "Sources: NYC DOHMH syndromic surveillance (EHDP-data, commit 547482b); NOAA GHCN-Daily USW00094728.", fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    f = FIG / "heat_ed_curve.png"
    fig.savefig(f, dpi=200)
    plt.close(fig)
    tag_srgb(f)
    return f


def chain():
    b = json.loads((DER / "bridge_results.json").read_text())
    h = json.loads((DER / "hyperlocal_results.json").read_text())
    links = [
        ("Street trees -> surface temp\n(CD, n=55, adj.)", b["link_a"]["adjusted"], "F per SD log trees/km2", "-"),
        ("Street trees -> surface temp\n(NTA, n=194, adj.)", b["nta"]["link_a_adjusted"], "F per SD log trees/km2", "-"),
        ("Vegetative cover -> surface temp\n(CD, adj.; not registered as link)", b["link_a"]["vegcover_adjusted"], "F per SD cover", "-"),
        ("Street trees within 50 m -> air temp\n(sensors, within NTA-day)", h["primary_trees50"], "C per 10 trees", "-"),
        ("Surface temp -> heat ED rate\n(CD, n=54, adj.)", b["link_b"]["adjusted"], "% per 1 F", "+"),
        ("Surface temp -> heat hosp. rate\n(NTA, n=194, adj.)", b["nta"]["link_b_hosp_adjusted"], "% per 1 F", "+"),
        ("Composed a x b: trees -> ED\nthrough surface temp (CD)", b["chain"], "% per SD log trees/km2", "-"),
        ("Total: trees -> heat ED rate\n(CD, adjusted)", b["total"]["adjusted"], "% per SD log trees/km2", "-"),
    ]
    fig, axes = plt.subplots(len(links), 1, figsize=(7.2, 7.6))
    for ax, (lab, v, unit, pred) in zip(axes, links):
        e = v.get("estimate", v.get("indirect_pct"))
        lo, hi = v["lo"], v["hi"]
        ok = (pred == "+" and lo > 0) or (pred == "-" and hi < 0)
        bad = (pred == "+" and hi < 0) or (pred == "-" and lo > 0)
        col = AQUA if ok else (ORANGE if bad else GREY)
        ax.errorbar([e], [0], xerr=[[e - lo], [hi - e]], fmt="o", color=col, ms=6, capsize=3, lw=1.6)
        ax.axvline(0, color=GREY, lw=0.8)
        span = max(abs(lo), abs(hi)) * 1.3
        ax.set_xlim(-span, span)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.text(-span, 0.55, lab, fontsize=7.5, color=INK, va="bottom")
        ax.text(span, 0.55, f"{e:+.2f} ({lo:+.2f} to {hi:+.2f}) {unit}; predicted {pred}", fontsize=7, color=INK2, va="bottom", ha="right")
        ax.set_ylim(-0.6, 1.6)
        ax.tick_params(axis="x", labelsize=7)
    fig.suptitle("Bridge chain: street trees -> temperature -> heat ED visits", x=0.01, ha="left", fontsize=10, color=INK)
    fig.text(0.01, 0.005, "Green: interval excludes 0 in the predicted direction. Orange: excludes 0 in the opposite direction. Grey: includes 0.\n"
             "Sources: 2015 Street Tree Census uvpi-gqnh; Hyperlocal Temperature Monitoring qdq3-9eqn; EHDP indicators 2141, 2143, 2443, hvi-nta.csv.",
             fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    f = FIG / "heat_bridge_chain.png"
    fig.savefig(f, dpi=200)
    plt.close(fig)
    tag_srgb(f)
    return f


if __name__ == "__main__":
    for fn in (shootings, ed):
        print(fn())
    if (DER / "hyperlocal_results.json").exists():
        print(chain())
