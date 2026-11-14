"""Galleries and artists: what open data show of where they are and how that has moved.

Sources and what each can show
  ZBP art dealers (NAICS 453920, 459920 from 2022): employer establishments by ZIP code, 1998 to 2023. The only
    series here with real history. Galleries with no payroll are absent; from 2017 cells under three are withheld.
  ZBP independent artists, writers and performers (711510): employers only, so mostly incorporated practices.
  ACS occupation group "arts, design, entertainment, sports and media" by residence, 2008-2012 and 2018-2022
    (acs_nta.py). A broad group: designers, editors, athletes and producers are in it.
  OpenStreetMap: tourism=gallery, shop=art, amenity=arts_centre, craft=artist, studio=art; current and
    as mapped on 1 January 2014, 2018 and 2022. History in OSM is the history of mapping, not of galleries.
  DCLA cultural organisations (u35m-9t32) and the Facilities Database (ji82-xba5): non-profits now on file.
Output data/derived/explore/art_*.csv, art_summary.json.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, RAW, points_to_nta, tract_table

AREAS = {
    "SoHo (10012)": ["10012"],
    "Tribeca (10013, 10007)": ["10013", "10007"],
    "Chelsea (10001, 10011)": ["10001", "10011"],
    "Lower East Side and East Village (10002, 10003, 10009)": ["10002", "10003", "10009"],
    "Midtown 57th Street (10019, 10022)": ["10019", "10022"],
    "Upper East Side (10021, 10028, 10065, 10075)": ["10021", "10028", "10065", "10075"],
    "Harlem (10026, 10027, 10030, 10031, 10035)": ["10026", "10027", "10030", "10031", "10035"],
    "Williamsburg and Greenpoint (11211, 11222, 11249)": ["11211", "11222", "11249"],
    "Bushwick (11206, 11221, 11237)": ["11206", "11221", "11237"],
    "Ridgewood (11385)": ["11385"],
    "DUMBO and Downtown Brooklyn (11201)": ["11201"],
    "Gowanus, Red Hook, Park Slope (11215, 11217, 11231)": ["11215", "11217", "11231"],
    "Long Island City (11101)": ["11101"],
    "South Bronx (10451, 10454, 10455)": ["10451", "10454", "10455"],
    "Jersey City (07302 to 07311)": ["07302", "07304", "07305", "07306", "07307", "07310", "07311"],
    "Hoboken (07030)": ["07030"],
}
YEARS = [1998, 2002, 2006, 2010, 2014, 2016, 2019, 2021, 2023]


def main():
    S = {}
    z = pd.read_csv(OUT / "zbp_extract.csv", dtype={"zip": str})
    nyc = ~z.zip.str.startswith("07")
    for series in ("art_dealers", "independent_artists"):
        zz = z[z.series == series]
        piv = zz.pivot_table(index="zip", columns="year", values="est", aggfunc="sum")
        rows = {}
        for a, zs in AREAS.items():
            rows[a] = piv.reindex(zs).sum(min_count=1)
        rows["New York City, all ZIP codes"] = zz[nyc].groupby("year").est.sum()
        t = pd.DataFrame(rows).T
        t.to_csv(OUT / f"art_zbp_{series}_areas.csv")
        S[series] = {a: {int(y): (None if pd.isna(v) else int(v)) for y, v in t.loc[a, YEARS].items()} for a in t.index}
        if series == "art_dealers":
            piv.to_csv(OUT / "art_zbp_art_dealers_zip.csv")
            top = {}
            for y in (1998, 2008, 2016, 2023):
                top[y] = piv[y].dropna().sort_values(ascending=False).head(8).astype(int).to_dict()
            S["art_dealers_top_zip"] = top
            # share of the city's art dealers in Manhattan below 96th Street is not computable by ZIP alone; give borough split
            b = zz[nyc].copy()
            b["pre"] = b.zip.str[:3]
            boro = b.pre.map(lambda p: "Manhattan" if p in ("100", "101", "102") else "Bronx" if p == "104" else
                             "Staten Island" if p == "103" else "Brooklyn" if p == "112" else "Queens")
            S["art_dealers_by_borough"] = {bb: {int(y): int(v) for y, v in g.groupby("year").est.sum().reindex(YEARS).fillna(0).items()}
                                           for bb, g in b.groupby(boro)}

    # OpenStreetMap
    names = tract_table().drop_duplicates("nta2020").set_index("nta2020").ntaname
    osm = {}
    cur = None
    for d in ("2014-01-01", "2018-01-01", "2022-01-01", "current"):
        f = RAW / "art" / f"osm_{d}.json"
        if not f.exists():
            osm[d] = None
            continue
        el = json.loads(f.read_text()).get("elements", [])
        rows = []
        for e in el:
            lat = e.get("lat", (e.get("center") or {}).get("lat"))
            lon = e.get("lon", (e.get("center") or {}).get("lon"))
            tg = e.get("tags", {})
            kind = ("gallery" if tg.get("tourism") == "gallery" else "art shop" if tg.get("shop") == "art" else
                    "arts centre" if tg.get("amenity") == "arts_centre" else "artist studio")
            rows.append({"lat": lat, "lon": lon, "kind": kind, "name": tg.get("name")})
        o = pd.DataFrame(rows).dropna(subset=["lat", "lon"])
        o["nta"] = points_to_nta(o.lon, o.lat)
        o["hudson"] = o.nta.isna() & (o.lon < -74.0) & (o.lat > 40.64) & (o.lat < 40.83) & (o.lon > -74.17)
        osm[d] = {"elements": len(o), "by_kind": o.kind.value_counts().to_dict(), "in_nyc": int(o.nta.notna().sum()),
                  "galleries_in_nyc": int(((o.kind == "gallery") & o.nta.notna()).sum()),
                  "galleries_west_of_hudson_in_box": int(((o.kind == "gallery") & o.hudson).sum())}
        if d == "current":
            cur = o
    S["osm"] = osm
    T = pd.DataFrame({"osm_galleries": cur[cur.kind == "gallery"].groupby("nta").size(),
                      "osm_art_places": cur.groupby("nta").size()})
    cur[cur.nta.notna() | cur.hudson].round(5).to_csv(OUT / "art_osm_points.csv", index=False)

    dc = pd.read_csv(RAW / "art" / "dcla.csv", dtype=str)
    S["dcla"] = {"n": len(dc), "discipline": dc.discipline.fillna("none").value_counts().head(8).to_dict(),
                 "with_coordinates": int(dc.latitude.notna().sum())}
    vis = dc[dc.discipline.isin(["Visual Arts", "Photography", "Museum", "Crafts", "New Media", "Architecture/Design"])]
    T["dcla_orgs"] = dc.groupby("nta").size()
    T["dcla_visual"] = vis.groupby("nta").size()
    fd = pd.read_csv(RAW / "art" / "facdb_cultural.csv", dtype=str)
    S["facdb"] = {"n": len(fd), "factype": fd.factype.value_counts().head(8).to_dict(), "datasource": fd.datasource.value_counts().to_dict()}

    a = pd.read_csv(OUT / "acs_nta.csv").set_index("nta")
    T = a[["pop", "arts_workers12", "arts_workers22", "arts_share12", "arts_share22"]].join(T).fillna(
        {"osm_galleries": 0, "osm_art_places": 0, "dcla_orgs": 0, "dcla_visual": 0})
    T["name"] = names.reindex(T.index)
    T["d_arts_workers"] = T.arts_workers22 - T.arts_workers12
    T["d_arts_share_pts"] = 100 * (T.arts_share22 - T.arts_share12)
    T.to_csv(OUT / "art_nta.csv")
    R = T[T["pop"] >= 5000]
    cols = ["name", "arts_workers12", "arts_workers22", "arts_share12", "arts_share22", "d_arts_workers", "d_arts_share_pts"]
    S["arts_occ_top_share"] = R.sort_values("arts_share22", ascending=False).head(12)[cols].round(3).to_dict("records")
    S["arts_occ_biggest_gain"] = R.sort_values("d_arts_workers", ascending=False).head(12)[cols].round(3).to_dict("records")
    S["arts_occ_biggest_loss"] = R.sort_values("d_arts_workers").head(10)[cols].round(3).to_dict("records")
    S["arts_occ_named"] = R[R.name.str.contains("SoHo|Chelsea|Lower East|East Village|Bushwick|Ridgewood|Mott Haven|Greenpoint|Williamsburg|Tribeca|Long Island City|Gowanus|Sunset Park \\(West\\)")][cols].round(3).to_dict("records")
    S["osm_top_nta"] = R.sort_values("osm_galleries", ascending=False).head(12)[["name", "osm_galleries", "osm_art_places"]].to_dict("records")
    S["arts_occ_totals"] = json.loads((OUT / "arts_occ.json").read_text())
    (OUT / "art_summary.json").write_text(json.dumps(S, indent=1, default=float))
    for k, v in S.items():
        print(k, json.dumps(v, default=float)[:2600])


if __name__ == "__main__":
    main()
