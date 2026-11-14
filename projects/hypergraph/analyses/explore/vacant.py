"""Vacant land in PLUTO (land use 11), 2002 to 2026: counts by version, what became of older vacant lots, clusters.

Input  ~/opt/nyc-concordance/explore/pluto/ (current table and DCP archive versions).
Output data/derived/explore/vacant_*.csv, vacant_summary.json.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from common import OUT, RAW, BORONAME, pluto, tract_table, xy_to_nta

BC = {"MN": "1", "BX": "2", "BK": "3", "QN": "4", "SI": "5"}
VERSIONS = [("02a", 2002), ("06c", 2006), ("10v1", 2010), ("14v2", 2014), ("18v2_1", 2018), ("24v4", 2024)]


def _bbl(b, block, lot):
    return b + block.astype(int).astype(str).str.zfill(5) + lot.astype(int).astype(str).str.zfill(4)


def load_old(v: str) -> pd.DataFrame:
    """bbl, landuse, ownertype, lotarea, bldgclass, x, y for one archive version."""
    zf = zipfile.ZipFile(RAW / "pluto" / {"02a": "nyc_pluto_02a.zip", "06c": "nyc_pluto_06c.zip", "10v1": "nyc_pluto_10v1.zip",
                                           "14v2": "nyc_pluto_14v2.zip", "18v2_1": "nyc_pluto_18v2_1_csv.zip",
                                           "24v4": "nyc_pluto_24v4_csv.zip"}[v])
    frames = []
    for name in zf.namelist():
        if not name.lower().endswith((".txt", ".csv")):
            continue
        raw = zf.read(name).decode("latin-1")
        if v == "02a":
            rows = list(csv.reader(io.StringIO(raw), skipinitialspace=True))
            rows = [r for r in rows if len(r) > 60]
            d = pd.DataFrame({"Borough": [r[0] for r in rows], "Block": [r[1] for r in rows], "Lot": [r[2] for r in rows],
                              "BldgClass": [r[23] for r in rows], "LandUse": [r[24] for r in rows],
                              "OwnerType": [r[26] for r in rows], "LotArea": [r[28] for r in rows],
                              "XCoord": [r[-12] for r in rows], "YCoord": [r[-11] for r in rows]})
        else:
            d = pd.read_csv(io.StringIO(raw), dtype=str, skipinitialspace=True, low_memory=False)
        d.columns = [c.strip().lower() for c in d.columns]
        d = d[["borough", "block", "lot", "bldgclass", "landuse", "ownertype", "lotarea", "xcoord", "ycoord"]].copy()
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    for c in d.columns:
        d[c] = d[c].astype(str).str.strip()
    d = d[d.borough.isin(BC)]
    for c in ("block", "lot", "lotarea", "xcoord", "ycoord", "landuse"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[d.block.notna() & d.lot.notna()]
    d["bbl"] = _bbl(d.borough.map(BC), d.block, d.lot)
    d["boro"] = d.borough.map(BC)
    return d.rename(columns={"xcoord": "x", "ycoord": "y"})


def summarise(d: pd.DataFrame, label: str, year: int) -> dict:
    v = d[d.landuse == 11]
    out = {"version": label, "year": year, "lots": len(d), "vacant_lots": len(v),
           "vacant_acres": float(v.lotarea.sum() / 43560), "city_owned_vacant_lots": int((v.ownertype == "C").sum())}
    for b, name in BORONAME.items():
        out[name] = int((v.boro == b).sum())
    return out


def main():
    cur = pluto().copy()
    cur["landuse"] = pd.to_numeric(cur.landuse, errors="coerce")
    rows, old = [], {}
    for v, yr in VERSIONS:
        d = load_old(v)
        old[v] = d
        rows.append(summarise(d, v, yr))
        print(rows[-1], flush=True)
    rows.append(summarise(cur, str(cur.version.dropna().iloc[0]), 2026))
    pd.DataFrame(rows).to_csv(OUT / "vacant_by_version.csv", index=False)

    vac = cur[(cur.landuse == 11) & cur.x.notna()].copy()
    summary = {"current_version": rows[-1], "by_bldgclass": vac.bldgclass.value_counts().head(12).to_dict()}

    # what became of the lots that were vacant in 2010 and in 2002
    cur_i = cur.drop_duplicates("bbl").set_index("bbl")
    fate = {}
    for v in ("02a", "10v1", "18v2_1"):
        o = old[v][old[v].landuse == 11].drop_duplicates("bbl")
        j = o.join(cur_i[["landuse", "yearbuilt", "unitsres"]].add_suffix("_now"), on="bbl")
        lu = j.landuse_now
        fate[v] = {"n": len(o), "still_vacant": int((lu == 11).sum()), "bbl_no_longer_exists": int(lu.isna().sum()),
                   "residential_now": int(lu.isin([1, 2, 3, 4]).sum()), "parking_now": int((lu == 10).sum()),
                   "open_space_now": int((lu == 9).sum()), "other_use_now": int(lu.isin([5, 6, 7, 8]).sum()),
                   "homes_on_them_now": float(j.unitsres_now[lu.isin([1, 2, 3, 4])].sum())}
    summary["fate"] = fate

    # per NTA, now and in 2010 / 2018
    by = vac.groupby("nta").agg(vacant_lots=("bbl", "size"), vacant_acres=("lotarea", lambda s: s.sum() / 43560),
                                city_owned=("ownertype", lambda s: int((s == "C").sum())))
    for v in ("10v1", "18v2_1"):
        # NTA of an old lot: that of the same BBL in current PLUTO, else from the old coordinates
        o = old[v][old[v].landuse == 11].drop_duplicates("bbl").copy()
        o["nta"] = o.bbl.map(cur_i.nta)
        need = o.nta.isna() & (o.x > 0)
        if need.any():
            o.loc[need, "nta"] = xy_to_nta(o.loc[need, "x"], o.loc[need, "y"])
        summary[f"nta_assigned_share_{v}"] = float(o.nta.notna().mean())
        by["vacant_lots_" + v] = o.groupby("nta").size()
    names = tract_table().drop_duplicates("nta2020").set_index("nta2020").ntaname
    by["name"] = names.reindex(by.index)
    by.fillna(0).sort_values("vacant_lots", ascending=False).to_csv(OUT / "vacant_nta.csv")

    # clusters: vacant lots linked when centroids are within 150 ft; components with 8 or more lots
    xy = vac[["x", "y"]].values
    pairs = cKDTree(xy).query_pairs(150.0, output_type="ndarray")
    n = len(vac)
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    _, lab = connected_components(g, directed=False)
    vac["cluster"] = lab
    v10 = set(old["10v1"][old["10v1"].landuse == 11].bbl)
    v02 = set(old["02a"][old["02a"].landuse == 11].bbl)
    vac["vac2010"] = vac.bbl.isin(v10)
    vac["vac2002"] = vac.bbl.isin(v02)
    summary["vacant_since_2010_share"] = float(vac.vac2010.mean())
    summary["vacant_since_2002_share"] = float((vac.vac2002 & vac.vac2010).mean())
    cl = []
    for c, gdf in vac.groupby("cluster"):
        if len(gdf) < 8:
            continue
        st = gdf.street.value_counts().head(3)
        cl.append({"cluster": int(c), "lots": len(gdf), "acres": float(gdf.lotarea.sum() / 43560),
                   "borough": BORONAME[gdf.boro.mode().iloc[0]], "nta": gdf.nta.mode().iloc[0] if gdf.nta.notna().any() else None,
                   "city_owned_share": float((gdf.ownertype == "C").mean()), "vacant_2010_share": float(gdf.vac2010.mean()),
                   "vacant_2002_share": float(gdf.vac2002.mean()),
                   "lat": float(gdf.latitude.mean()), "lon": float(gdf.longitude.mean()),
                   "streets": "; ".join(f"{k} ({v})" for k, v in st.items()),
                   "zoning": "; ".join(gdf.zonedist1.fillna("none").value_counts().head(2).index),
                   "top_owner": str(gdf.ownername.fillna("").value_counts().index[0])[:40]})
    C = pd.DataFrame(cl).sort_values("lots", ascending=False)
    C["nta_name"] = C.nta.map(names)
    C.to_csv(OUT / "vacant_clusters.csv", index=False)
    summary["clusters_8plus"] = len(C)
    vac[["bbl", "x", "y", "latitude", "longitude", "lotarea", "ownertype", "nta", "cluster", "vac2010", "vac2002", "address", "bldgclass"]].to_csv(
        OUT / "vacant_lots.csv", index=False)
    (OUT / "vacant_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print(json.dumps(summary, indent=1, default=float))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 60)
    print(C.head(45)[["lots", "acres", "borough", "nta_name", "city_owned_share", "vacant_2010_share", "vacant_2002_share", "streets", "zoning", "top_owner"]].to_string())


if __name__ == "__main__":
    main()
