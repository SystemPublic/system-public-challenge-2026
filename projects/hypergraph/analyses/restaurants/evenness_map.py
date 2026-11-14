"""Maps for docs/restaurants.md: by 2020 NTA in Manhattan, (a) raw critical violations per routine
initial inspection, (b) the adjusted rate ratio from the registered harshness model, (c) the
adjusted rate ratio of routine inspections per restaurant-year (exploratory). Source: Underlay
snapshot v1.0.0 via evenness_test.py outputs; boundaries 9nt8-h7nd."""
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import Normalize, TwoSlopeNorm

import common as c

g = gpd.read_file(c.DER / "nta2020.geojson")
g = g[g.boroname == "Manhattan"]
t = pd.read_csv(c.DER / "evenness_nta.csv")
m = g.merge(t.drop(columns=["ntaname"]), on="nta2020", how="left")
fig, ax = plt.subplots(1, 3, figsize=(13, 8))
specs = [("crit_per_initial_raw", "Raw: critical violations\nper initial inspection", "viridis", Normalize(1.6, 2.4)),
         ("harsh_rr_adj", "Adjusted rate ratio, critical violations\n(registered model; permutation p = 0.31)", "RdBu_r", TwoSlopeNorm(1, 0.85, 1.15)),
         ("freq_rr_adj", "Adjusted rate ratio, initial inspections\nper restaurant-year (exploratory)", "RdBu_r", TwoSlopeNorm(1, 0.85, 1.15))]
for a, (col, title, cmap, norm) in zip(ax, specs):
    m.plot(column=col, ax=a, cmap=cmap, norm=norm, legend=True, edgecolor="white", linewidth=0.4,
           missing_kwds={"color": "0.88", "label": "fewer than 20 restaurants"}, legend_kwds={"shrink": 0.6})
    a.set_title(title, fontsize=10)
    a.set_axis_off()
fig.suptitle("Manhattan NTAs (2020), routine inspections 2024-01 to 2026-06, Underlay snapshot v1.0.0; grey: fewer than 20 restaurants", fontsize=9)
print(c.save_fig(fig, "evenness_map.png"))
