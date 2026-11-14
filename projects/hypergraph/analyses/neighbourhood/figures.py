"""Figures for the neighbourhood claims. Reads data/derived/neighbourhood/*_results.json and tract tables.

Colours: NYC estimates in blue (#2a78d6), research estimates in orange (#eb6834), third series aqua (#1baf7a).
PNG files are tagged with an sRGB profile afterwards (sips) when available.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "neighbourhood"
FIG = ROOT / "figures" / "neighbourhood"
NYC, RES, THIRD, INK, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 10,
                     "axes.titleweight": "bold", "figure.dpi": 150, "savefig.dpi": 200, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb"})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / name
    fig.savefig(p, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    prof = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
    if shutil.which("sips") and Path(prof).exists():
        subprocess.run(["sips", "--embedProfile", prof, str(p)], capture_output=True)
    print("wrote", p.relative_to(ROOT))


def forest(ax, rows, null=1.0, log=True, xlabel=""):
    """rows: list of (label, est, lo, hi, colour)."""
    for i, (lab, e, lo, hi, col) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round")
        ax.plot([e], [y], "o", color=col, ms=6, mec="#fcfcfb", mew=1.5)
        ax.text(hi, y + 0.22, f"  {e:.2f} [{lo:.2f}, {hi:.2f}]", va="bottom", ha="left", fontsize=7.5, color=MUTED)
    ax.axvline(null, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8)
    if log:
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        lo_, hi_ = min(r[2] for r in rows), max(r[3] for r in rows)
        cand = (0.5, 1.0, 2.0, 3.0, 4.0) if hi_ / max(lo_, 1e-9) > 2.5 else (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0)
        ticks = [v for v in cand if min(lo_, null) * 0.97 <= v <= hi_ * 1.05]
        ax.set_xticks(ticks)
    ax.set_xlabel(xlabel)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.6, len(rows) - 0.2)


def vacant():
    r = json.loads((D / "vacant_shootings_results.json").read_text())
    t = pd.DataFrame(r["poverty_tercile_by_quintile"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw={"width_ratios": [1, 1.1], "wspace": 0.95})
    for col, (lev, lab) in zip(["#b3a9f0", "#7d6ee0", "#3b2c9e"], [("low", "low poverty"), ("middle", "middle poverty"), ("high", "high poverty")]):
        s = t[t["pov_t"] == lev].sort_values("vac_q")
        a1.plot(s["vac_q"] + 1, s["rate"], "-o", color=col, lw=2, ms=5, mec="#fcfcfb")
        a1.text(5.12, s["rate"].iloc[-1], lab, color=INK, va="center", fontsize=8)
    a1.set_xticks([1, 2, 3, 4, 5])
    a1.set_xlim(0.8, 6.2)
    a1.set_xlabel("quintile of tract vacant-land share (MapPLUTO land use 11)")
    a1.set_ylabel("shootings per 10,000 residents per year")
    a1.set_title("Shootings 2019-2024 by vacant-land quintile", loc="left")
    a1.grid(axis="y", color="#e6e5e0", lw=0.6)
    e = lambda k, lab, c=NYC: (lab, r[k]["estimate"], r[k]["lo"], r[k]["hi"], c)  # noqa: E731
    rows = [("Philadelphia block groups, assault\n(Branas et al. 2013, per category)", 1.18, 1.12, 1.25, RES),
            e("unadjusted_per_quintile", "NYC unadjusted, per quintile"),
            e("adjusted_per_quintile", "NYC adjusted, per quintile (registered)"),
            e("adjusted_per_quintile_no_staten_island", "NYC adjusted, without Staten Island"),
            e("adjusted_plus_race_per_quintile", "NYC adjusted + race/ethnicity"),
            e("adjusted_per_sd", "NYC adjusted, per SD of share"),
            e("adjusted_private_per_sd", "NYC private vacant land, per SD"),
            e("adjusted_city_owned_per_sd", "NYC City-owned vacant land, per SD")]
    forest(a2, rows, xlabel="incidence rate ratio (log scale)")
    a2.set_title("Research beside NYC (IRR, 95% CI)", loc="left")
    fig.text(0.01, -0.04, "Adjusted: negative binomial, offset log population, poverty, log density, borough. Sources: MapPLUTO 26v2 (64uk-42ks); "
             "NYPD Shootings 5ucz-vwe8; ACS 2018-2022. Philadelphia outcome is aggravated assault, not shootings.", fontsize=7, color=MUTED)
    save(fig, "vacant_shootings.png")


def rodents():
    r = json.loads((D / "rodents_asthma_results.json").read_text())
    d = pd.read_csv(D / "rodents_asthma_uhf.csv")
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(15, 4.4), gridspec_kw={"width_ratios": [1, 1.1, 0.8], "wspace": 1.05})
    a1.scatter(d["rodents_bldg_pct"], d["asthma_ed_5_17"], s=28, color=NYC, edgecolor="#fcfcfb", lw=1, zorder=3)
    for _, row in d.iterrows():
        if row["GEONAME"] in ("East Harlem", "Central Harlem - Morningside Heights", "Crotona - Tremont", "Bayside - Little Neck",
                              "Greenwich Village - Soho", "Southeast Queens", "Kingsbridge - Riverdale"):
            a1.annotate(row["GEONAME"], (row["rodents_bldg_pct"], row["asthma_ed_5_17"]), fontsize=6.5, color=MUTED,
                        xytext=(4, 2), textcoords="offset points")
    a1.set_yscale("log")
    a1.set_yticks([20, 50, 100, 200, 400])
    a1.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
    a1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a1.set_xlabel("homes with mice or rats in the building, % (NYCHVS 2017)")
    a1.set_ylabel("asthma ED visits age 5-17 per 10,000 (2017, log)")
    a1.set_title(f"42 UHF neighbourhoods, rho = {r['primary']['spearman_rho']:.2f}", loc="left")
    a1.grid(color="#e6e5e0", lw=0.6)
    e = lambda k, lab, part="adjusted": (lab, r[k][part]["estimate"], r[k][part]["lo"], r[k][part]["hi"], NYC)  # noqa: E731
    rows = [e("primary", "HVS rodents, unadjusted", "unadjusted"),
            e("primary", "HVS rodents, adjusted (registered)"),
            e("primary_plus_cockroach", "  + cockroaches"),
            e("adult_outcome", "HVS rodents, adult ED outcome"),
            e("chs_inside", "CHS mice/rats inside (2012)"),
            e("inspections_vs_latest", "DOHMH rat-activity share (2022-24)"),
            e("complaints_vs_latest", "311 rodent complaints (2022-24)")]
    forest(a2, rows, null=0.0, log=False, xlabel="change in log ED rate per SD of rodent measure")
    a2.set_title("NYC ecological estimates (95% CI)", loc="left")
    res = [("Mouse allergen x10, any care\n(Torjusen 2013)", 1.87, 1.21, 2.88, RES),
           ("High mouse allergen, ED\n(Matsui 2006)", 2.1, 1.1, 4.1, RES),
           ("Infestation, asthma\n(PMID 31103883)", 2.1, 1.1, 3.8, RES)]
    forest(a3, res, xlabel="odds ratio (log scale)")
    a3.set_title("Household research (graph)", loc="left")
    fig.text(0.01, -0.06, "Adjusted: OLS, controls poverty % and renter housing problems %, HC3 SE, n = 42. Rows 6-7 use asthma ED 2023 and "
             "poverty 2019-23. Sources: EHDP-data commit 547482b; DOHMH Rodent Inspection p937-wjvj; 311 erm2-nwe9. "
             "Research and NYC estimates are on different scales and are shown side by side, not compared numerically.",
             fontsize=7, color=MUTED, wrap=True)
    save(fig, "rodents_asthma.png")


def noise():
    import geopandas as gpd
    r = json.loads((D / "noise311_results.json").read_text())
    df = pd.read_csv(D / "noise311_tracts.csv", dtype={"GEOID": str})
    g = gpd.read_file(D / "tracts.geojson").set_crs(4326, allow_override=True).to_crs(2263)
    g = g.merge(df[["GEOID", "res_rate", "noise_mean_db", "d_logrent"]], left_on="geoid", right_on="GEOID", how="left")
    fig = plt.figure(figsize=(16, 5.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.0], wspace=0.75)
    for i, (col, lab, cmap, vmin, vmax) in enumerate([
            ("res_rate", "Residential noise complaints\nper 1,000 residents per year, 2022-24", "Blues", 0, float(df["res_rate"].quantile(0.95))),
            ("noise_mean_db", "Modelled transport noise, tract mean dB(A)\n(US DOT noise map 2020, LAeq 24 h)", "Purples", 40, 60)]):
        ax = fig.add_subplot(gs[0, i])
        g.plot(ax=ax, color="#e6e5e0", lw=0)
        g.dropna(subset=[col]).plot(ax=ax, column=col, cmap=cmap, vmin=vmin, vmax=vmax, lw=0, legend=True,
                                    legend_kwds={"shrink": 0.6, "orientation": "horizontal", "pad": 0.02})
        ax.set_axis_off()
        ax.set_title(lab, loc="left", fontsize=9)
    ax = fig.add_subplot(gs[0, 2])
    names = {"z_noise_mean_db": "modelled transport noise", "z_d_logrent": "rent change 2008-12 to 2018-22",
             "z_d_nhw": "change in non-Hispanic white share", "z_log_bars": "on-premises liquor licences (log)",
             "z_log_density": "population density (log)", "z_poverty": "poverty share"}
    o = r["ols"]
    ys = list(names)
    for j, (k, col, off) in enumerate([("res", NYC, 0.17), ("street", THIRD, -0.17)]):
        for i, v in enumerate(ys):
            y = len(ys) - 1 - i + off
            b = o[k][v]
            ax.plot([b["lo"], b["hi"]], [y, y], color=col, lw=2, solid_capstyle="round")
            ax.plot([b["b"]], [y], "o", color=col, ms=5, mec="#fcfcfb", mew=1.2)
    ax.axvline(0, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.set_yticks(range(len(ys)))
    ax.set_yticklabels([names[v] for v in ys][::-1], fontsize=8)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("change in log(1 + complaints per 1,000) per SD, 95% CI")
    ax.set_title("Joint model with borough effects", loc="left", pad=28)
    ax.plot([], [], color=NYC, lw=2, label="residential complaints")
    ax.plot([], [], color=THIRD, lw=2, label="street/sidewalk + vehicle")
    ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 0.995), ncol=2, borderaxespad=0.2)
    c = r["contrast_res"]
    fig.text(0.01, -0.03, f"Registered contrast (rent change minus modelled noise, residential): {c['estimate']:.2f} [{c['lo']:.2f}, {c['hi']:.2f}]. "
             "Research dose-response for comparison: road traffic noise and hypertension OR 1.11 per 10 dB(A) (PMID 24952459). "
             "Sources: 311 erm2-nwe9; geo.dot.gov NTAD noise 2020; NYS SLA 9s3h-dpkz; ACS 2008-12, 2018-22.", fontsize=7, color=MUTED)
    save(fig, "noise311.png")


if __name__ == "__main__":
    for name in sys.argv[1:] or ["vacant", "rodents", "noise"]:
        globals()[name]()
