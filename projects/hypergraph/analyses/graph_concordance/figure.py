"""Figure: the concordance matrix. Lower triangle: agreement with the literature. Upper triangle: the city correlation."""
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

import common as C
from indicators import BY_KEY, KEYS

M = pd.read_csv(C.OUT / "matrix_pairs.csv")
ORDER = ["pm25", "no2", "black_carbon", "ozone", "traffic", "noise", "surface_temp", "green_cover", "tree_shade", "park_access", "walkability", "pop_density",
         "ac", "crowding", "owner_occupied", "housing_problems", "leaks", "cockroaches", "rodents", "vacant_land", "evictions",
         "poverty", "unemployment", "high_school", "limited_english", "foreign_born", "insurance", "shootings", "alcohol_outlets",
         "transit_commute", "walk_commute", "bike_commute", "car_commute", "exercise", "smoking", "binge_drinking", "sugary_drinks",
         "asthma_adult", "asthma_child", "obesity", "diabetes", "depression", "distress", "psych_hosp", "good_health", "premature_death",
         "preterm", "low_birthweight", "infant_death", "pedestrian_injury", "heat_ed", "lead", "walking_difficulty", "cognitive_difficulty",
         "hearing_difficulty", "vision_difficulty"]
assert sorted(ORDER) == sorted(KEYS)
ix = {k: i for i, k in enumerate(ORDER)}
n = len(ORDER)
cat = np.full((n, n), np.nan)   # lower triangle
rho = np.full((n, n), np.nan)   # upper triangle
# categories: 0 unmapped end, 1 no findings, 2 findings below threshold or mixed, 3 agree, 4 disagree
for _, r in M.iterrows():
    i, j = sorted([ix[r["a"]], ix[r["b"]]])
    if not r["mappable"]:
        c = 0
    elif r["n_findings"] == 0:
        c = 1
    elif r["qualifies"] != True:  # noqa: E712
        c = 2
    else:
        c = 3 if np.sign(r["rho_deciding"]) == r["lit_sign"] else 4
    cat[j, i] = c
    rho[i, j] = r["rho_deciding"]
fig, ax = plt.subplots(figsize=(13.5, 13))
cm = ListedColormap(["#c9c9c9", "#ffffff", "#f3e3a2", "#2f6fb0", "#d1495b"])
ax.imshow(cat, cmap=cm, vmin=-0.5, vmax=4.5, interpolation="nearest")
im = ax.imshow(rho, cmap="PuOr_r", vmin=-1, vmax=1, interpolation="nearest", alpha=0.9)
for k in range(n + 1):
    ax.axhline(k - 0.5, color="#e6e6e6", lw=0.4)
    ax.axvline(k - 0.5, color="#e6e6e6", lw=0.4)
for g in (12, 21, 29, 37):
    ax.axhline(g - 0.5, color="#555555", lw=0.9)
    ax.axvline(g - 0.5, color="#555555", lw=0.9)
labs = [BY_KEY[k]["label"] + ("  [no concept]" if not BY_KEY[k]["concepts"] else "") for k in ORDER]
ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels(labs, rotation=90, fontsize=7)
ax.set_yticklabels(labs, fontsize=7)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
q = M[M["qualifies"] == True]  # noqa: E712
na, nd = int((np.sign(q["rho_deciding"]) == q["lit_sign"]).sum()), int((np.sign(q["rho_deciding"]) != q["lit_sign"]).sum())
leg = [Patch(fc="#2f6fb0", label=f"city sign agrees with the literature ({na} pairs)"),
       Patch(fc="#d1495b", label=f"city sign opposite to the literature ({nd})"),
       Patch(fc="#f3e3a2", ec="#bbbbbb", label=f"findings exist, but under 3 studies or under 80% one sign ({int(((M['n_findings'] > 0) & (M['qualifies'] != True)).sum())})"),
       Patch(fc="#ffffff", ec="#999999", label=f"both concepts exist, the graph holds no finding ({int((M['mappable'] & (M['n_findings'] == 0)).sum())})"),
       Patch(fc="#c9c9c9", label=f"an indicator has no concept in the graph ({int((~M['mappable']).sum())})")]
ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.0, -0.27), fontsize=9, frameon=False, title="Below the diagonal: System Public Graph against the city", title_fontsize=9, alignment="left")
cax = ax.inset_axes([0.56, -0.335, 0.42, 0.012])
cb = fig.colorbar(im, cax=cax, orientation="horizontal")
cax.set_title("Above the diagonal: Spearman correlation across 42 UHF\nneighbourhoods, poverty partialled out", fontsize=9, loc="left")
cb.ax.tick_params(labelsize=8)
ax.set_title("Does New York's neighbourhood ecology agree with the published literature, pair by pair?\n"
             "56 city indicators, 1,540 pairs; literature sign from the System Public Graph (API v1.0, 12 Nov 2026)", fontsize=11, loc="left")
out = C.ROOT / "figures" / "graph" / "concordance_matrix.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(out)], check=True, capture_output=True)
print(out)
