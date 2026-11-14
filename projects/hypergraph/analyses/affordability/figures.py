"""Figures for docs/affordability.md. Saved with matplotlib; tag with the sRGB profile afterwards (sips)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/derived/affordability"; F = ROOT / "figures/affordability"; F.mkdir(parents=True, exist_ok=True)
VERM, BLUE, GREY, DARK = "#D55E00", "#0072B2", "#B8B8B8", "#333333"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
p = pd.read_csv(D / "furman_panel.csv", dtype={"region_id": str, "year": str})
s = pd.read_csv(D / "sba_table.csv", dtype={"region_id": str}).set_index("region_id")
now = pd.read_csv(D / "sba_now.csv", dtype={"region_id": str}).set_index("region_id")
ex = json.load(open(D / "explore.json")); res = json.load(open(D / "gentrification_results.json"))
sb = p[p.region_type == "Sub-Borough Area"]; city = p[p.region_type == "City"].set_index("year")
grp = now.group
COL = {"gentrified": VERM, "low start, not gentrified": BLUE, "other 33": GREY}

# 1. trajectories of rent rank
yrs = ["2000"] + [str(y) for y in range(2005, 2025)]
R = sb[sb.year.isin(yrs)].pivot(index="year", columns="region_id", values="rent_gross_med_adj")
R.index = R.index.astype(int); R = R.sort_index()
sm = R.copy(); a = R.loc[2005:]; sm.loc[2005:] = a.rolling(3, center=True, min_periods=2).mean()
rank = sm.rank(axis=1, method="average")
fig, ax = plt.subplots(figsize=(9.2, 6.6))
for g, lw, al, z in [("other 33", 0.7, 0.75, 1), ("low start, not gentrified", 1.0, 0.8, 2), ("gentrified", 2.0, 1.0, 3)]:
    for rid in grp.index[grp == g]:
        ax.plot(rank.index, rank[rid], color=COL[g], lw=lw, alpha=al, zorder=z)
        ax.plot([2000], [rank.loc[2000, rid]], "o", ms=3 if g != "gentrified" else 4.5, color=COL[g], zorder=z)
ends = rank.loc[2024, grp.index[grp == "gentrified"]].sort_values()
ypos = []; 
for rid, y in ends.items():
    yy = y if not ypos or y - ypos[-1] >= 1.9 else ypos[-1] + 1.9; ypos.append(yy)
    ax.annotate(f"{s.name[rid]}  ({int(s.rent_rank00[rid])} to {int(s.rent_rank_end[rid])})", (2024, y), xytext=(2024.6, yy), fontsize=8, color=VERM, va="center",
                arrowprops=dict(arrowstyle="-", color=VERM, lw=0.5))
ax.axhline(22.5, color=DARK, lw=0.6, ls=":"); ax.text(2000.2, 23.1, "the 22 cheapest areas in 2000 lie below this line", fontsize=7.5, color=DARK)
ax.axvspan(2000.15, 2004.85, color="#F3F3F3", zorder=0); ax.text(2002.5, 54, "no data\n2001 to 2004", ha="center", va="top", fontsize=7.5, color="#777777")
ax.set_xlim(1999.5, 2035); ax.set_ylim(0, 56); ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2024])
ax.set_yticks([1, 10, 20, 30, 40, 50, 55]); ax.set_ylabel("rank of median gross rent among 55 areas (1 = cheapest)")
ax.spines["bottom"].set_bounds(2000, 2024)
h = [plt.Line2D([], [], color=VERM, lw=2), plt.Line2D([], [], color=BLUE, lw=1), plt.Line2D([], [], color=GREY, lw=0.8)]
ax.legend(h, ["low rent in 2000; rent and college\nshare then grew faster than the city's (8)", "low rent in 2000; did not meet\nboth conditions (14)", "the other 33 areas"],
          loc="center left", bbox_to_anchor=(0.685, 0.5), frameon=False, fontsize=7.5)
ax.set_title("Rent rank of New York's 55 sub-borough areas, 2000 to 2024", loc="left", fontsize=11)
fig.text(0.01, 0.01, "Median gross rent of all tenants, constant dollars, three-year moving average from 2005. Labels give the rank in 2000 and in 2022-2024.\nSource: NYU Furman Center CoreData (census 2000 and American Community Survey).", fontsize=7, color="#555555")
fig.tight_layout(rect=(0, 0.045, 1, 1)); fig.savefig(F / "rent_rank_trajectories.png", dpi=200); plt.close(fig)

# 2. the definition: rent growth against college change
c = res["claim1"]["city"]
fig, ax = plt.subplots(figsize=(7.2, 5.6))
for g in ["other 33", "low start, not gentrified", "gentrified"]:
    i = grp.index[grp == g]
    ax.scatter(s.coll_change[i], s.rent_growth[i] * 100, s=34, color=COL[g], edgecolor="white", lw=0.5, zorder=3, label=g)
ax.axvline(c["coll_change"], color=DARK, lw=0.7, ls="--"); ax.axhline(c["rent_growth"] * 100, color=DARK, lw=0.7, ls="--")
ax.text(c["coll_change"] + 0.4, -6, f"city: +{c['coll_change']:.1f} points", fontsize=7.5, color=DARK); ax.text(-3.5, c["rent_growth"] * 100 + 2, f"city: +{c['rent_growth']*100:.0f}%", fontsize=7.5, color=DARK)
lab = list(grp.index[grp == "gentrified"]) + [i for i in s.index if s.name[i] in ("Park Slope/Carroll Gardens", "Astoria", "South Crown Heights", "Mott Haven/Hunts Point", "Kingsbridge Heights/Mosholu", "Greenwich Village/Financial District", "Lower East Side/Chinatown")]
for i in lab:
    ax.annotate(s.name[i].split("/")[0], (s.coll_change[i], s.rent_growth[i] * 100), xytext=(4, 3), textcoords="offset points", fontsize=7, color=COL[grp[i]] if grp[i] != "other 33" else "#666666")
ax.set_xlabel("change in share of adults with a college degree, 2000 to 2022-2024 (points)"); ax.set_ylabel("growth of real median gross rent, 2000 to 2022-2024 (%)")
ax.set_ylim(-10, 150); ax.legend(frameon=False, fontsize=8, loc="upper left", labels=["the other 33 areas", "low rent in 2000, not gentrified (14)", "low rent in 2000, gentrified (8)"])
ax.set_title(f"Rent growth and growth in college share move together (Spearman {res['claim1']['spearman_rent_growth_college_change']:.2f})", loc="left", fontsize=10)
fig.tight_layout(); fig.savefig(F / "rent_growth_vs_college.png", dpi=200); plt.close(fig)

# 3. affordability now
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.6), gridspec_kw={"width_ratios": [1.25, 1]})
BC = {"1": "#0072B2", "2": "#D55E00", "3": "#009E73", "4": "#CC79A7", "5": "#E69F00"}; BN = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
for b in BC:
    i = [r for r in now.index if r[0] == b]
    a1.scatter(now.income[i] / 1000, now.burden_med[i], s=30, color=BC[b], edgecolor="white", lw=0.5, label=BN[b], zorder=3)
a1.axhline(30, color=DARK, lw=0.7, ls="--"); a1.text(205, 30.3, "30% of income", fontsize=7.5, ha="right")
for i in now.sort_values("burden_med").index[[0, 1, 2, -1, -2, -3, -4, -5]]:
    a1.annotate(now.name[i].split("/")[0], (now.income[i] / 1000, now.burden_med[i]), xytext=(4, 2), textcoords="offset points", fontsize=7, color="#555555")
a1.set_xlabel("median household income, 2022-2024 (thousand dollars)"); a1.set_ylabel("median share of income that renters pay in rent (%)")
a1.legend(frameon=False, fontsize=8); a1.set_title("(a) Rent takes the largest share of income where incomes are lowest", loc="left", fontsize=9.5)
af = ex["affordability"]; zo = ex["zori"]
bars = [("all\ntenants,\n2009-11", af["all_tenants_2009_11"]["n_at_median"] / 55), ("all\ntenants,\n2022-24", af["all_tenants_2022_24"]["n_at_median"] / 55),
        ("recent\nmovers,\n2006-10", af["recent_movers_2006_10"]["n_at_median"] / 55), ("recent\nmovers,\n2020-24", af["recent_movers_2020_24"]["n_at_median"] / 55),
        ("asking\nrent,\n2025-26", zo["n_at_median_now"] / zo["n_zip_now"])]
txt = [f"{af['all_tenants_2009_11']['n_at_median']} of 55", f"{af['all_tenants_2022_24']['n_at_median']} of 55", f"{af['recent_movers_2006_10']['n_at_median']} of 55",
       f"{af['recent_movers_2020_24']['n_at_median']} of 55", f"{zo['n_at_median_now']} of {zo['n_zip_now']}\nZIP codes"]
x = np.arange(len(bars)); a2.bar(x, [b[1] * 100 for b in bars], color=[GREY, DARK, GREY, DARK, VERM], width=0.65)
for xi, b, t in zip(x, bars, txt): a2.text(xi, b[1] * 100 + 1.5, t, ha="center", fontsize=8)
a2.set_xticks(x); a2.set_xticklabels([b[0] for b in bars], fontsize=7.5); a2.set_ylim(0, 100); a2.set_ylabel("share of areas where the median rent is within budget (%)")
a2.set_title("(b) Areas a household at the city median income\ncan rent in at 30% of income. At half the median: none.", loc="left", fontsize=9.5)
fig.tight_layout(); fig.savefig(F / "affordability_now.png", dpi=200); plt.close(fig)

# 4. poor residents: change in count by area
E19 = ["2017", "2018", "2019"]   # before the 2022 change of boundaries (see boundary_check.py)
poor19 = sb[sb.year.isin(E19)].groupby("region_id").apply(lambda x: (x.pop_pov_pct * x.pop_num / 100).mean())
d = ((poor19 - s.poor00) / 1000).sort_values()
bc = json.load(open(D / "boundary_check.json"))["end_2017_19"]["totals_pct"]
fig, ax = plt.subplots(figsize=(7.4, 8.6))
ax.barh(range(len(d)), d.values, color=[COL[grp[i]] for i in d.index], height=0.75)
ax.set_yticks(range(len(d))); ax.set_yticklabels([s.name[i] for i in d.index], fontsize=6.8); ax.axvline(0, color=DARK, lw=0.6)
for t, i in zip(ax.get_yticklabels(), d.index): t.set_color(COL[grp[i]] if grp[i] != "other 33" else "#444444")
ax.set_xlabel("change in residents below the poverty line,\n2000 to 2017-2019 (thousands)")
t = res["claim2"]["totals"]
ax.set_title("Change in the number of poor residents, by area", loc="left", fontsize=10)
ax.text(0.04, 0.97, f"gentrified (8): {bc['gentrified']:.0f}%\nlow start, not gentrified (14): {bc['other_low']:.0f}%\nother 33 areas: {bc['other_33']:.0f}%",
        transform=ax.transAxes, ha="left", va="top", fontsize=8.5, color=DARK)
h = [plt.Rectangle((0, 0), 1, 1, color=COL[g]) for g in COL]; ax.legend(h, ["gentrified", "low rent in 2000, not gentrified", "other 33 areas"], frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0.02, 0.88))
ax.margins(y=0.01); fig.tight_layout(); fig.savefig(F / "poor_count_change.png", dpi=200); plt.close(fig)
print("ok")
