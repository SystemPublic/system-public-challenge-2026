"""Figures for docs/explore.md. Reads data/derived/explore/, writes figures/explore/*.png (sRGB tagged)."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIG, OUT, ntas, tag_srgb

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab", "#0d366b"]
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False, "savefig.facecolor": SURF})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    f = FIG / name
    fig.savefig(f, dpi=200, bbox_inches="tight")
    plt.close(fig)
    tag_srgb(f)
    print("wrote", f.name)


def base(ax, g, fc="#f0efec"):
    g.plot(ax=ax, facecolor=fc, edgecolor="#ffffff", linewidth=0.3)
    ax.set_axis_off()
    ax.set_aspect("equal")


def fig_film():
    g = ntas()
    s = pd.read_csv(OUT / "film_segments.csv")
    s = s.groupby(["x", "y"], as_index=False)[["n", "n_early", "n_late"]].sum()
    c = pd.read_csv(OUT / "film_nta_change.csv")
    fig, axs = plt.subplots(1, 3, figsize=(13, 5.4))
    for ax, col, ttl, div in ((axs[0], "n_early", "2012 to 2015 (four years)", 4), (axs[1], "n_late", "2023 to 2026 (3.6 years)", 3.6)):
        base(ax, g)
        d = s[s[col] > 0]
        ax.scatter(d.x, d.y, s=np.sqrt(d[col] / div) * 2.2, color=BLUE, alpha=0.35, linewidths=0)
        ax.set_title(ttl, fontsize=10, loc="left")
        ax.set_xlim(975000, 1025000)
        ax.set_ylim(170000, 232000)
    for n in (4, 40, 160):
        axs[0].scatter([], [], s=np.sqrt(n) * 2.2, color=BLUE, alpha=0.5, linewidths=0, label=f"{n} permits a year")
    axs[0].legend(loc="upper left", frameon=False, fontsize=8)
    ax = axs[2]
    m = g.merge(c[["nta", "share_change_pts", "total"]], on="nta", how="left")
    m["v"] = m.share_change_pts.where(m.total >= 40)
    base(ax, g)
    vmax = 1.6
    m.dropna(subset=["v"]).plot(ax=ax, column="v", cmap=matplotlib.colors.LinearSegmentedColormap.from_list("d", [ORANGE, "#f0efec", BLUE]),
                                vmin=-vmax, vmax=vmax, edgecolor="#ffffff", linewidth=0.3, legend=True,
                                legend_kwds={"shrink": 0.5, "label": "change in share of located permits, points\n(2023-25 minus 2012-15; scale clipped at 1.6)"})
    ax.set_xlim(975000, 1025000)
    ax.set_ylim(170000, 232000)
    ax.set_title("Change in each NTA's share", fontsize=10, loc="left")
    for nta, lab, dx, dy in (("BK0101", "Greenpoint +4.6", 6000, 9000), ("BK0102", "Williamsburg -1.6", 9000, -2000), ("MN0102", "Tribeca +1.5", -17000, -6000)):
        r = g[g.nta == nta].geometry.centroid.iloc[0]
        ax.annotate(lab, (r.x, r.y), (r.x + dx, r.y + dy), fontsize=8, color=INK, arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.6})
    fig.suptitle("Street segments held for film and television shoots (MOME film permits, located through PLUTO; Manhattan, north Brooklyn, west Queens)",
                 fontsize=10.5, x=0.01, ha="left")
    fig.text(0.01, 0.0, "Each dot is a block face named on shooting permits; area is proportional to permits a year. 83% of segment mentions were located. "
             "24 June to 31 December 2022 is missing from every copy of the table.", fontsize=7.5, color=INK2)
    save(fig, "film_map.png")


def fig_vacant():
    g = ntas()
    v = pd.read_csv(OUT / "vacant_by_version.csv")
    lots = pd.read_csv(OUT / "vacant_lots.csv")
    fig = plt.figure(figsize=(13, 6))
    ax = fig.add_axes([0.03, 0.12, 0.3, 0.72])
    boros = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
    cols = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA]
    bottom = np.zeros(len(v))
    for b, col in zip(boros, cols):
        ax.bar(range(len(v)), v[b], bottom=bottom, color=col, width=0.62, label=b, edgecolor=SURF, linewidth=1.2)
        bottom += v[b].values
    for i, t in enumerate(v.vacant_lots):
        ax.text(i, t + 500, f"{t:,}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(range(len(v)))
    ax.set_xticklabels([f"{y}\n{ver}" for y, ver in zip(v.year, v.version)], fontsize=8)
    ax.set_ylabel("tax lots with land use 11 (vacant)")
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title("Vacant lots by PLUTO version", fontsize=10, loc="left")
    ax2 = fig.add_axes([0.36, 0.02, 0.64, 0.9])
    base(ax2, g)
    old = lots[lots.vac2010]
    new = lots[~lots.vac2010]
    ax2.scatter(old.x, old.y, s=1.6, color=BLUE, alpha=0.6, linewidths=0, label=f"vacant in 2010 and now ({len(old):,})")
    ax2.scatter(new.x, new.y, s=1.6, color=ORANGE, alpha=0.7, linewidths=0, label=f"vacant now, not in 2010 ({len(new):,})")
    cl = pd.read_csv(OUT / "vacant_clusters.csv")
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 2263, always_xy=True)
    picks = [("FOX BEACH", "1 Oakwood Beach", 12000, -14000), ("BEACH 44", "2 Edgemere", -2000, -14000), ("UNION STREET", "3 Columbia St waterfront", -52000, 4000),
             ("GRAHAM BOULEVARD", "4 Midland Beach", 16000, -6000), ("NOEL AVENUE", "5 Gerritsen Beach", 6000, -16000),
             ("STREET (65)", "6 Hamilton Beach", 14000, -12000), ("NIELSEN", "7 Charleston", -8000, 16000)]
    for key, lab, dx, dy in picks:
        r = cl[cl.streets.str.contains(key, regex=False)].iloc[0]
        x, y = tr.transform(r.lon, r.lat)
        ax2.annotate(lab, (x, y), (x + dx, y + dy), fontsize=8.5, color=INK, arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.7})
    lg = ax2.legend(frameon=False, fontsize=8.5, loc="upper left", markerscale=6)
    ax2.set_title("Vacant lots in PLUTO 26v2, and seven clusters named in the text", fontsize=10, loc="left")
    save(fig, "vacant_map.png")


def fig_coffee():
    g = ntas()
    t = pd.read_csv(OUT / "coffee_nta.csv")
    s = json.loads((OUT / "coffee_summary.json").read_text())
    fig = plt.figure(figsize=(13, 5.6))
    ax = fig.add_axes([0.0, 0.02, 0.4, 0.88])
    m = g.merge(t[["nta", "coffee_per_10k", "pop"]], on="nta", how="left")
    m["v"] = m.coffee_per_10k.where(m["pop"] >= 5000)
    base(ax, g, fc="#ffffff")
    bins = [0, 0.0001, 1, 2.5, 5, 10, 100]
    labs = ["none", "under 1", "1 to 2.5", "2.5 to 5", "5 to 10", "10 or more"]
    cols = ["#f0efec"] + SEQ[1:]
    m["b"] = pd.cut(m.v, bins, labels=False, include_lowest=True, right=False)
    for i, (lab, col) in enumerate(zip(labs, cols)):
        mm = m[m.b == i]
        if len(mm):
            mm.plot(ax=ax, color=col, edgecolor="#ffffff", linewidth=0.3)
        ax.scatter([], [], marker="s", s=60, color=col, label=lab)
    ax.legend(frameon=False, fontsize=8, loc="upper left", title="coffee and tea shops\nper 10,000 residents", title_fontsize=8, alignment="left")
    ax.set_title("Density by NTA, November 2026", fontsize=10, loc="left")
    ax = fig.add_axes([0.45, 0.13, 0.25, 0.72])
    r = t[t["pop"] >= 5000]
    ax.scatter(100 * r.ba_share, r.independent_per_10k, s=14, color=BLUE, alpha=0.7, linewidths=0.5, edgecolors=SURF)
    ax.set_yscale("symlog", linthresh=1)
    ax.set_yticks([0, 1, 2, 5, 10, 25])
    ax.set_yticklabels(["0", "1", "2", "5", "10", "25"])
    ax.set_xlabel("adults with a bachelor's degree, % (ACS 2018-2022)")
    ax.set_ylabel("independent coffee shops per 10,000 residents")
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    sp = s["spearman"]["independent_per_10k"]["ba_share"]
    ax.set_title(f"Independents and education\nSpearman {sp['rho']:.2f} ({sp['lo']:.2f} to {sp['hi']:.2f}), n = {sp['n']}", fontsize=10, loc="left")
    for nm in ("Midtown-Times Square", "SoHo-Little Italy-Hudson Square", "Greenpoint"):
        q = r[r.name == nm].iloc[0]
        ax.annotate(nm.split("-")[0], (100 * q.ba_share, q.independent_per_10k), (100 * q.ba_share - 30, q.independent_per_10k * 1.1), fontsize=7.5,
                    color=INK2, arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5})
    ax = fig.add_axes([0.76, 0.13, 0.23, 0.72])
    z = {int(k): v for k, v in s["zbp_snack_beverage_by_year"].items()}
    ys = sorted(z)
    ax.plot(ys, [z[y] for y in ys], color=BLUE, linewidth=2)
    ax.set_ylim(0, 4000)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.axvline(2002, color=MUTED, linewidth=0.6, linestyle=":")
    ax.text(2002.4, 300, "NAICS revision", fontsize=7.5, color=MUTED)
    ax.set_title("Snack and nonalcoholic beverage bars,\nNew York City (Census ZBP)", fontsize=10, loc="left")
    ax.set_ylabel("employer establishments")
    ax.text(ys[-1], z[ys[-1]] + 90, f"{z[ys[-1]]:,}", ha="right", fontsize=8, color=INK2)
    ax.text(ys[0], z[ys[0]] + 110, f"{z[ys[0]]:,}", ha="left", fontsize=8, color=INK2)
    save(fig, "coffee.png")


def fig_art():
    t = pd.read_csv(OUT / "art_zbp_art_dealers_areas.csv", index_col=0)
    t.columns = t.columns.astype(int)
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axs[0]
    sel = [("Upper East Side", "Upper East Side", BLUE), ("Chelsea", "Chelsea", ORANGE), ("Midtown", "Midtown, 57th Street", AQUA),
           ("SoHo", "SoHo", YELLOW), ("Lower East Side", "Lower East Side, East Village", MAGENTA), ("Tribeca", "Tribeca", GREEN),
           ("Bushwick", "Bushwick", VIOLET), ("Williamsburg", "Williamsburg, Greenpoint", RED)]
    for key, lab, col in sel:
        row = t[t.index.str.startswith(key)].iloc[0]
        ax.plot(row.index, row.values, color=col, linewidth=2)
        last = row.dropna()
        ax.text(2023.4, last.iloc[-1], f"{lab} {int(last.iloc[-1])}", fontsize=8, va="center", color=INK2)
    ax.set_xlim(1998, 2034)
    ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2023])
    ax.set_ylim(0, 180)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylabel("art dealers with employees (ZIP Code Business Patterns)")
    ax.axvline(2017, color=MUTED, linewidth=0.6, linestyle=":")
    ax.text(2017.2, 174, "from 2017, cells under 3 withheld", fontsize=7.5, color=MUTED)
    ax.set_title("Art dealers by district, 1998 to 2023", fontsize=10, loc="left")
    # nudge overlapping end labels
    txt = sorted(ax.texts[:-1], key=lambda q: q.get_position()[1])
    prev = -99
    for q in txt:
        x, y = q.get_position()
        if y - prev < 7:
            y = prev + 7
            q.set_position((x, y))
        prev = y
    ax = axs[1]
    a = pd.read_csv(OUT / "art_nta.csv")
    a = a[a["pop"] >= 5000]
    top = pd.concat([a.sort_values("d_arts_workers").head(8), a.sort_values("d_arts_workers").tail(8)])
    ax.barh(range(len(top)), top.d_arts_workers, color=[ORANGE if v < 0 else BLUE for v in top.d_arts_workers], height=0.62)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([n[:34] for n in top.name], fontsize=8)
    ax.axvline(0, color="#c3c2b7", linewidth=0.8)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("change in residents working in arts, design, entertainment,\nsports and media occupations, ACS 2008-2012 to 2018-2022")
    ax.set_title("Where arts workers live: largest losses and gains", fontsize=10, loc="left")
    fig.tight_layout()
    save(fig, "galleries_artists.png")


if __name__ == "__main__":
    fig_film()
    fig_vacant()
    fig_coffee()
    fig_art()
