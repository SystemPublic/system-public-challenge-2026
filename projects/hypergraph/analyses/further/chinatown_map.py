"""Figure for further-chinatown-shift: change in Asian-alone residents 2010 to 2020 by 2010 tract, three areas."""
import json, io
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from PIL import Image, ImageCms
from analyses.further import chinatown_analysis as A
ROOT = A.ROOT; EXT = Path.home() / "opt/nyc-concordance/chinatown/data"
sets = A.sets
gdf = gpd.read_file(EXT / "cb2010/gz_2010_36_140_00_500k.shp"); gdf["geoid"] = gdf.GEO_ID.str[-11:]
gdf = gdf[gdf.geoid.str[:5].isin(["36061", "36047", "36081"])].to_crs(4326).set_index("geoid")
allt = sorted(set(A.t10.index) & set(gdf.index))
a10 = A.t10.loc[allt, "asian_alone"].astype(float); a20 = A.apportion(A.t20.asian_alone, allt)
gdf = gdf.loc[allt]; gdf["d"] = a20.values - a10.values; gdf["a10"] = a10.values
panels = [("Manhattan: Chinatown and Lower East Side", (-74.025, -73.955, 40.695, 40.745), "chinatown_B1", None),
          ("Brooklyn: Sunset Park", (-74.04, -73.97, 40.615, 40.665), "sunset_park_core", "sunset_park_all"),
          ("Queens: Flushing", (-73.88, -73.79, 40.72, 40.79), "flushing_core", "flushing_all")]
norm = TwoSlopeNorm(vmin=-1500, vcenter=0, vmax=1500)
fig, axs = plt.subplots(1, 3, figsize=(15, 6.2))
for ax, (title, (x0, x1, y0, y1), core, whole) in zip(axs, panels):
    sub = gdf.cx[x0:x1, y0:y1]
    sub.plot(column="d", cmap="RdBu_r", norm=norm, ax=ax, edgecolor="#9a9a9a", linewidth=0.3)
    if whole is None:
        gdf.loc[sets[core]].boundary.plot(ax=ax, color="black", linewidth=1.6)
    else:
        gdf.loc[sets[whole]].boundary.plot(ax=ax, color="#555555", linewidth=0.9)
        gdf.loc[sets[core]].boundary.plot(ax=ax, color="black", linewidth=1.8)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2))); ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(''); ax.set_ylabel(''); ax.axis('off'); ax.set_title(title, fontsize=11)
    for sp in ax.spines.values(): sp.set_visible(False)
sm = plt.cm.ScalarMappable(norm=norm, cmap="RdBu_r"); cb = fig.colorbar(sm, ax=axs, orientation="horizontal", fraction=0.04, pad=0.04, aspect=50)
cb.set_label("Change in Asian-alone residents, 2010 to 2020, per 2010 census tract (persons; red = increase, blue = decrease)")
r = json.load(open(A.D / "chinatown_results.json"))
sp, fl, ct = r["sunset_asian"], r["flushing_asian"], r["chinatown_B1_asian_alone"]["all"]
fig.suptitle("Asian-alone population change 2010 to 2020. Bold outline: registered set (left), 8th Avenue core (centre), Flushing core (right); thin dark outline: all tracts of the place", fontsize=10, y=0.93)
fig.text(0.01, -0.02, f"Chinatown set (23 tracts): {ct['pct_M1']:+.1f}% (bootstrap 95% {ct['boot95'][0]:+.1f} to {ct['boot95'][1]:+.1f}).  Sunset Park core {sp['core']['pct_M1']:+.1f}%, periphery {sp['periphery']['pct_M1']:+.1f}%, difference {sp['diff_M1']:+.1f} points (95% {sp['diff_boot95'][0]:+.1f} to {sp['diff_boot95'][1]:+.1f}).  Flushing {fl['all']['pct_M1']:+.1f}%.  "
         "Sources: 2010 and 2020 PL 94-171 tract counts; 2020 counts apportioned to 2010 tracts by land area; cartographic boundaries 2010.", fontsize=8)
buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=200, bbox_inches="tight"); buf.seek(0)
im = Image.open(buf).convert("RGB")
prof = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
out = ROOT / "figures/further/chinatown_shift_map.png"; im.save(out, icc_profile=prof, dpi=(200, 200)); print(out)
