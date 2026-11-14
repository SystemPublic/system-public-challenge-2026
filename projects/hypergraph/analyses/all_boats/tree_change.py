"""Street trees per 2020 census tract in the 2005 and 2015 street tree censuses.

Exposure only. Reads no outcome. Living trees: 2005 status other than Dead; 2015 status Alive.
Tree points are downloaded (latitude, longitude, status, diameter) from NYC Open Data
29bw-z7pj and uvpi-gqnh to ~/opt/nyc-concordance/all_boats/ and joined to the project's
2020 tract polygons.
"""
import json, sys
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata
BIG = Path.home() / "opt/nyc-concordance/all_boats"
OUT = ROOT / "data/derived/all_boats"
tr = gpd.read_file(ROOT / "data/derived/neighbourhood/tracts.geojson")[["geoid", "geometry"]]
res = {}
for ds, yr in (("29bw-z7pj", 2005), ("uvpi-gqnh", 2015)):
    d = pd.read_csv(BIG / f"{ds}.csv")
    d = d[d.latitude.notna() & d.longitude.notna()]
    alive = d[d.status != "Dead"] if yr == 2005 else d[d.status == "Alive"]
    pts = gpd.GeoDataFrame(alive[["tree_dbh"]], geometry=gpd.points_from_xy(alive.longitude, alive.latitude), crs=4326)
    j = gpd.sjoin(pts, tr, predicate="within", how="inner")
    res[f"trees{yr}"] = j.groupby("geoid").size()
    res[f"small{yr}"] = j[j.tree_dbh <= 3].groupby("geoid").size()
    print(yr, "rows", len(d), "living", len(alive), "in a tract", len(j))
df = pd.DataFrame(res).reindex(tr.geoid).fillna(0).astype(int).reset_index().rename(columns={"index": "geoid"})
df.to_csv(OUT / "tree_counts_tracts.csv", index=False)
src = [socrata.source_record(ds, {"$select": "latitude,longitude,status,tree_dbh", "$limit": 1000000}) for ds in ("29bw-z7pj", "uvpi-gqnh")]
(OUT / "tree_sources.json").write_text(json.dumps(src, indent=1))
print(df.describe().T)
