"""Build viz/data/explore_data.js for viz/explore.html: one record per 2020 NTA with simplified outline and measures.

The page loads the file with a script tag (no fetch), so it opens from the file system. All paths are relative.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, ROOT, ntas, xy_to_nta

W, H = 760, 760
MEASURES = [  # key, label, unit text, decimals
    ("film_recent", "Film and TV shoots a year, 2023-25", "permits a year", 1),
    ("film_early", "Film and TV shoots a year, 2012-15", "permits a year", 1),
    ("vacant_lots", "Vacant lots (PLUTO 26v2)", "lots", 0),
    ("vacant_per_km2", "Vacant lots per square km", "lots per sq km", 1),
    ("vacant_change", "Change in vacant lots since 2010", "lots", 0),
    ("new_restaurants", "Restaurants and cafes first inspected since Sept 2024", "places", 0),
    ("new_share", "Share of restaurants that are new", "%", 0),
    ("coffee_per_10k", "Coffee and tea shops per 10,000 residents", "per 10,000", 1),
    ("indep_coffee", "Independent coffee and tea shops", "shops", 0),
    ("chain_share", "Chain share of coffee shops", "%", 0),
    ("osm_galleries", "Galleries mapped in OpenStreetMap", "galleries", 0),
    ("arts_share", "Residents in arts and media occupations, 2018-22", "% of employed", 1),
    ("arts_change", "Change in arts and media workers since 2008-12", "people", 0),
    ("dining_out", "Sidewalk and roadway cafe licences", "licences", 0),
    ("rent", "Median gross rent, 2018-22", "$ a month", 0),
    ("rent_change", "Rent change, 2008-12 to 2018-22", "%", 0),
    ("income", "Median household income, 2018-22", "$", 0),
    ("ba_share", "Adults with a bachelor's degree", "%", 0),
    ("share_25_34", "Residents aged 25 to 34", "%", 1),
]
UNUSUAL = ["film_recent", "vacant_per_km2", "vacant_change", "new_share", "coffee_per_10k", "chain_share", "osm_galleries",
           "arts_share", "arts_change", "dining_out", "rent", "rent_change", "income", "ba_share", "share_25_34"]


def main():
    g = ntas().copy()
    minx, miny, maxx, maxy = g.total_bounds
    sc = min(W / (maxx - minx), H / (maxy - miny))

    def path(geom):
        geom = geom.simplify(220)
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        out = []
        for p in polys:
            if p.area < 2.0e5:
                continue
            xs, ys = p.exterior.coords.xy
            pts = [f"{(x - minx) * sc:.1f},{(maxy - y) * sc:.1f}" for x, y in zip(xs, ys)]
            out.append("M" + "L".join(pts) + "Z")
        return "".join(out)

    film = pd.read_csv(OUT / "film_nta_change.csv").set_index("nta")
    fy = pd.read_csv(OUT / "film_nta_year.csv").set_index("nta")
    vac = pd.read_csv(OUT / "vacant_nta.csv").set_index("nta")
    shops = pd.read_csv(OUT / "shops_nta.csv").set_index("nta")
    cof = pd.read_csv(OUT / "coffee_nta.csv").set_index("nta")
    art = pd.read_csv(OUT / "art_nta.csv").set_index("nta")
    seg = pd.read_csv(OUT / "film_segments.csv")
    seg = seg.groupby(["street", "c1", "c2", "x", "y"], as_index=False)[["n", "n_late"]].sum()
    seg["nta"] = xy_to_nta(seg.x, seg.y)
    cl = pd.read_csv(OUT / "vacant_clusters.csv")

    D = pd.DataFrame(index=g.nta)
    D["film_recent"] = film.late_per_year
    D["film_early"] = film.early_per_year
    D["vacant_lots"] = vac.vacant_lots
    D["vacant_change"] = vac.vacant_lots - vac.vacant_lots_10v1
    D["new_restaurants"] = shops.restaurants_new
    D["restaurants"] = shops.restaurants
    D["new_share"] = 100 * shops.new_share.where(shops.restaurants >= 30)
    D["dining_out"] = shops.dining_out
    D["coffee_per_10k"] = cof.coffee_per_10k
    D["indep_coffee"] = cof.independent
    D["chain_share"] = 100 * cof.chain_share.where(cof.coffee >= 8)
    D["osm_galleries"] = art.osm_galleries
    D["arts_share"] = 100 * art.arts_share22
    D["arts_change"] = art.d_arts_workers
    D["rent"] = cof.rent22
    D["rent_change"] = 100 * (np.exp(cof.d_logrent) - 1)
    D["income"] = cof.income
    D["ba_share"] = 100 * cof.ba_share
    D["share_25_34"] = 100 * cof.share_25_34
    D["pop"] = cof["pop"]
    km2 = g.set_index("nta").km2
    D["vacant_per_km2"] = D.vacant_lots.fillna(0) / km2
    for c in ("film_recent", "film_early", "vacant_lots", "new_restaurants", "dining_out", "indep_coffee", "osm_galleries", "vacant_change"):
        D[c] = D[c].fillna(0)
    res = D["pop"] >= 5000
    pct = {}
    for k in [m[0] for m in MEASURES]:
        r = D.loc[res, k].rank(pct=True) * 100
        pct[k] = r
    years = [c for c in fy.columns if c not in ("2022", "2026", "2020")]
    recs = []
    for _, row in g.iterrows():
        n = row.nta
        d = D.loc[n]
        rec = {"id": n, "name": row["name"], "boro": row.boro, "d": path(row.geometry), "res": bool(res.loc[n]),
               "pop": None if pd.isna(d["pop"]) else int(d["pop"]), "m": {}, "p": {}}
        for k, _, _, dec in MEASURES:
            v = d[k]
            rec["m"][k] = None if pd.isna(v) or not res.loc[n] and k not in ("film_recent", "film_early", "vacant_lots", "osm_galleries", "new_restaurants") else round(float(v), dec if dec else 1)
            if res.loc[n] and n in pct[k].index and not pd.isna(pct[k].loc[n]):
                rec["p"][k] = int(round(pct[k].loc[n]))
        rec["film_years"] = [[int(y), int(fy.loc[n, y])] for y in years] if n in fy.index else []
        s = seg[seg.nta == n].sort_values("n", ascending=False).head(3)
        rec["blocks"] = [[f"{a.title()} between {b.title()} and {c.title()}", int(k)] for a, b, c, k in s[["street", "c1", "c2", "n"]].itertuples(index=False)]
        c = cl[cl.nta == n].sort_values("lots", ascending=False).head(1)
        rec["cluster"] = None if c.empty else {"lots": int(c.lots.iloc[0]), "streets": c.streets.iloc[0].title(),
                                               "since2010": int(round(100 * c.vacant_2010_share.iloc[0])),
                                               "lat": round(float(c.lat.iloc[0]), 5), "lon": round(float(c.lon.iloc[0]), 5)}
        recs.append(rec)
    med = {k: (None if pd.isna(D.loc[res, k].median()) else round(float(D.loc[res, k].median()), 1)) for k, *_ in MEASURES}
    out = {"built": "2026-11-13", "w": W, "h": int((maxy - miny) * sc) + 1, "measures": [list(m) for m in MEASURES], "unusual": UNUSUAL,
           "median": med, "n_res": int(res.sum()), "ntas": recs}
    f = ROOT / "viz" / "data" / "explore_data.js"
    f.write_text("window.EXPLORE = " + json.dumps(out, separators=(",", ":")) + ";\n")
    print("wrote", f.relative_to(ROOT), f.stat().st_size, "bytes", len(recs), "NTAs")


if __name__ == "__main__":
    main()
