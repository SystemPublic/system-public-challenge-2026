"""Film permits 2012 to 2026: where productions hold streets, how that has moved, and what the streets are like.

Input  ~/opt/nyc-concordance/explore/film_wayback/*.csv (archived exports, 2012 to June 2022),
       film/film_current.csv (tg4x-b46p, 2023 onward), pluto/pluto_current.csv.
Output data/derived/explore/film_*.csv / film_summary.json.

Method. The table has no coordinates. Each permit lists street segments as "STREET between A and B".
A gazetteer of intersections is built from PLUTO alone: two tax lots on differently named streets whose
centroids lie within 450 ft mark a place where those streets may meet; the intersection of two streets
(per borough) is the median midpoint of their closest lot pairs (those within 100 ft of the closest pair).
Only street pairs that a permit names as crossing are ever looked up. A permit's borough field holds one
borough although its segments may lie in another, so the other boroughs are tried when the first fails. A segment is located when both of its
intersections are found and lie within 4,000 ft of each other. The lots that front the segment are the
lots addressed on that street whose centroid projects between the two intersections, within 200 ft.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from common import OUT, RAW, BORONAME, norm_street, pluto, tract_table

BORO_CODE = {"Manhattan": "1", "Bronx": "2", "Brooklyn": "3", "Queens": "4", "Staten Island": "5"}
COLS = ["eventid", "eventtype", "startdatetime", "enddatetime", "enteredon", "eventagency", "parkingheld", "borough",
        "communityboard_s", "policeprecinct_s", "category", "subcategoryname", "country", "zipcode_s"]
RADIUS = 450.0
ALIAS = {"AVENUE OF THE AMERICAS": "6 AVENUE", "AVENUE OF AMERICAS": "6 AVENUE", "SIXTH AVENUE": "6 AVENUE",
         "ADAM CLAYTON POWELL BOULEVARD": "7 AVENUE", "ADAM CLAYTON POWELL JR BOULEVARD": "7 AVENUE",
         "MALCOLM X BOULEVARD": "LENOX AVENUE", "FREDERICK DOUGLAS BOULEVARD": "8 AVENUE",
         "FREDERICK DOUGLASS BOULEVARD": "8 AVENUE", "FIRST AVENUE": "1 AVENUE", "SECOND AVENUE": "2 AVENUE",
         "THIRD AVENUE": "3 AVENUE", "FOURTH AVENUE": "4 AVENUE", "FIFTH AVENUE": "5 AVENUE", "SEVENTH AVENUE": "7 AVENUE",
         "EIGHTH AVENUE": "8 AVENUE", "NINTH AVENUE": "9 AVENUE", "TENTH AVENUE": "10 AVENUE", "ELEVENTH AVENUE": "11 AVENUE",
         "TWELFTH AVENUE": "12 AVENUE", "BLEEKER STREET": "BLEECKER STREET", "DELANCY STREET": "DELANCEY STREET",
         "HUMBOLT STREET": "HUMBOLDT STREET", "MCGUINESS BOULEVARD": "MCGUINNESS BOULEVARD",
         "N HENRY STREET": "NORTH HENRY STREET", "RIVERSIDE DR": "RIVERSIDE DRIVE", "MACDONOUGH STREET": "MAC DONOUGH STREET"}


def canon(s: str) -> str:
    s = norm_street(s)
    return ALIAS.get(s, s)


FULL_YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2023, 2024, 2025]


def load() -> pd.DataFrame:
    frames = []
    for f, fmt in (("film_wayback/film_20220204105500.csv", "%m/%d/%Y %I:%M:%S %p"),
                   ("film_wayback/film_20220924230956.csv", "%m/%d/%Y %I:%M:%S %p"),
                   ("film/film_current.csv", None)):
        d = pd.read_csv(RAW / f, dtype=str)
        d.columns = COLS
        d["start"] = pd.to_datetime(d.startdatetime, format=fmt, errors="coerce")
        d["src"] = f
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d = d[d.start.notna() & d.borough.isin(BORO_CODE)]
    d = d.drop_duplicates("eventid", keep="last")
    d["year"] = d.start.dt.year
    return d


def segments(text: str) -> list[tuple[str, str, str]]:
    out = []
    for part in str(text).split(","):
        m = re.match(r"\s*(.+?)\s+between\s+(.+?)\s+and\s+(.+?)\s*$", part, flags=re.I)
        if m:
            out.append(tuple(canon(x) for x in m.groups()))
    return out


def gazetteer(p: pd.DataFrame) -> dict:
    """{(boro, streetA, streetB)} -> (x, y) for A < B."""
    gaz = {}
    for b, g in p[p.x.notna()].groupby("boro"):
        xy = g[["x", "y"]].values
        st = g["street"].values
        codes, names = pd.factorize(st)
        pairs = cKDTree(xy).query_pairs(RADIUS, output_type="ndarray")
        ca, cb = codes[pairs[:, 0]], codes[pairs[:, 1]]
        keep = ca != cb
        pairs, ca, cb = pairs[keep], ca[keep], cb[keep]
        dist = np.linalg.norm(xy[pairs[:, 0]] - xy[pairs[:, 1]], axis=1)
        mid = (xy[pairs[:, 0]] + xy[pairs[:, 1]]) / 2
        df = pd.DataFrame({"a": np.minimum(ca, cb), "b": np.maximum(ca, cb), "d": dist, "mx": mid[:, 0], "my": mid[:, 1]})
        df = df[df.d <= df.groupby(["a", "b"]).d.transform("min") + 100]
        agg = df.groupby(["a", "b"]).agg(mx=("mx", "median"), my=("my", "median"), n=("mx", "size"))
        agg.index = pd.MultiIndex.from_tuples([tuple(sorted((names[i], names[j]))) for i, j in agg.index])
        for (l, h), r in agg.iterrows():
            gaz[(b, l, h)] = (r.mx, r.my)
        print("gazetteer", b, len(agg), flush=True)
    return gaz


def main():
    d = load()
    cover = {"first": str(d.start.min()), "last": str(d.start.max()),
             "gap": "24 June 2022 to 31 December 2022 is in neither the archived copies nor the current table",
             "by_year_all_types": {int(k): int(v) for k, v in d.year.value_counts().sort_index().items()},
             "event_types": d.eventtype.value_counts().to_dict()}
    s = d[d.eventtype == "Shooting Permit"].copy()
    cover["shooting_permits"] = len(s)
    cover["shooting_by_year"] = {int(k): int(v) for k, v in s.year.value_counts().sort_index().items()}
    cover["shooting_by_category"] = s.category.value_counts().to_dict()
    cover["category_by_year"] = {str(y): g.category.value_counts().to_dict() for y, g in s.groupby("year")}
    cover["borough_by_year"] = {str(y): g.borough.value_counts().to_dict() for y, g in s.groupby("year")}

    # ZIP codes (a permit may list several; it is counted once in each)
    z = s[["eventid", "year", "zipcode_s"]].copy()
    z["zip"] = z.zipcode_s.fillna("").str.split(",")
    z = z.explode("zip")
    z["zip"] = z.zip.str.strip()
    z = z[z.zip.str.match(r"^\d{5}$", na=False)]
    zy = z.groupby(["zip", "year"]).eventid.nunique().unstack(fill_value=0)
    zy.to_csv(OUT / "film_zip_year.csv")

    # segments
    p = pluto().copy()
    p["street"] = p["street"].map(lambda v: ALIAS.get(v, v))
    gaz = gazetteer(p)
    by_street = {k: g for k, g in p[p.x.notna()].groupby(["boro", "street"])}
    seg_rows = []
    for eid, yr, cat, boro, text in s[["eventid", "year", "category", "borough", "parkingheld"]].itertuples(index=False):
        for (st, a, b) in segments(text):
            seg_rows.append((eid, yr, cat, BORO_CODE[boro], st, a, b))
    seg = pd.DataFrame(seg_rows, columns=["eventid", "year", "category", "boro", "street", "c1", "c2"])
    # a segment is the same whichever way its cross streets are listed
    lo = np.where(seg.c1 < seg.c2, seg.c1, seg.c2)
    hi = np.where(seg.c1 < seg.c2, seg.c2, seg.c1)
    seg["c1"], seg["c2"] = lo, hi
    seg = seg.drop_duplicates(["eventid", "boro", "street", "c1", "c2"])
    uniq = seg.groupby(["boro", "street", "c1", "c2"]).size().rename("n").reset_index()
    print("segment mentions", len(seg), "unique", len(uniq), flush=True)

    def pt(b, s1, s2):
        return gaz.get((b, s1, s2) if s1 < s2 else (b, s2, s1))

    recs = []
    lotsets = {}
    for i, (b0, st, c1, c2, n) in enumerate(uniq.itertuples(index=False)):
        rec = {"boro": b0, "street": st, "c1": c1, "c2": c2, "located": False}
        A = B = None
        for b in [b0] + [x for x in "12345" if x != b0]:
            A, B = pt(b, st, c1), pt(b, st, c2)
            if A and B and 60 < np.linalg.norm(np.array(B) - np.array(A)) < 4000:
                break
            A = B = None
        if A and B:
            A, B = np.array(A), np.array(B)
            L = np.linalg.norm(B - A)
            g = by_street.get((b, st))
            if 60 < L < 4000 and g is not None:
                v = (B - A) / L
                rel = g[["x", "y"]].values - A
                t = rel @ v
                perp = np.abs(rel[:, 0] * v[1] - rel[:, 1] * v[0])
                m = (t > -40) & (t < L + 40) & (perp < 200)
                lots = g[m]
                mid = (A + B) / 2
                rec.update(located=True, x=mid[0], y=mid[1], length_ft=L, n_lots=int(m.sum()))
                if len(lots):
                    nta = lots.nta.dropna()
                    rec["nta"] = nta.mode().iloc[0] if len(nta) else None
                    yb = lots.yearbuilt[lots.yearbuilt > 1700]
                    rec["yearbuilt_median"] = float(yb.median()) if len(yb) else np.nan
                    rec["pre1940"] = float((yb < 1940).mean()) if len(yb) else np.nan
                    rec["floors_median"] = float(lots.numfloors[lots.numfloors > 0].median()) if (lots.numfloors > 0).any() else np.nan
                    lu = lots.landuse.fillna("NA").str.zfill(2)
                    for code in ("01", "02", "03", "04", "05", "06", "11"):
                        rec["lu" + code] = float((lu == code).mean())
                    rec["histdist"] = float(lots.histdist.notna().mean())
                    lotsets[(b, st, c1, c2)] = lots.bbl.tolist()
        recs.append(rec)
    R = pd.DataFrame(recs)
    # segments with no fronting lot still need an NTA: take the nearest lot
    need = R.located & R.nta.isna()
    if need.any():
        pp = p[p.x.notna() & p.nta.notna()]
        _, idx = cKDTree(pp[["x", "y"]].values).query(R.loc[need, ["x", "y"]].values)
        R.loc[need, "nta"] = pp.nta.values[idx]
    uniq = uniq.merge(R, on=["boro", "street", "c1", "c2"])
    seg = seg.merge(uniq.drop(columns="n"), on=["boro", "street", "c1", "c2"])
    cover["segment_mentions"] = len(seg)
    cover["segment_mentions_located"] = int(seg.located.sum())
    cover["unique_segments"] = len(uniq)
    cover["unique_segments_located"] = int(uniq.located.sum())
    cover["located_share_by_boro"] = {BORONAME[b]: float(g.located.mean()) for b, g in seg.groupby("boro")}

    # most used blocks: number of distinct permits naming the segment
    top = uniq.sort_values("n", ascending=False).head(60).copy()
    rec_recent = seg[seg.year >= 2023].groupby(["boro", "street", "c1", "c2"]).eventid.nunique().rename("n_2023_26")
    rec_early = seg[seg.year <= 2015].groupby(["boro", "street", "c1", "c2"]).eventid.nunique().rename("n_2012_15")
    top = top.join(rec_recent, on=["boro", "street", "c1", "c2"]).join(rec_early, on=["boro", "street", "c1", "c2"])
    names = tract_table().drop_duplicates("nta2020").set_index("nta2020").ntaname
    top["nta_name"] = top.nta.map(names)
    top["borough"] = top.boro.map(BORONAME)
    top[["borough", "street", "c1", "c2", "n", "n_2012_15", "n_2023_26", "nta", "nta_name", "yearbuilt_median", "floors_median",
         "lu06", "histdist", "located"]].to_csv(OUT / "film_top_blocks.csv", index=False)
    rt = uniq.join(rec_recent, on=["boro", "street", "c1", "c2"]).sort_values("n_2023_26", ascending=False).head(40).copy()
    rt["nta_name"] = rt.nta.map(names)
    rt["borough"] = rt.boro.map(BORONAME)
    rt[["borough", "street", "c1", "c2", "n", "n_2023_26", "nta", "nta_name", "yearbuilt_median", "lu06", "located"]].to_csv(
        OUT / "film_top_blocks_recent.csv", index=False)

    # NTA by year: permits with at least one located segment in the NTA
    loc = seg[seg.located & seg.nta.notna()]
    ny = loc.groupby(["nta", "year"]).eventid.nunique().unstack(fill_value=0)
    ny.to_csv(OUT / "film_nta_year.csv")
    tot_located = loc.groupby("year").eventid.nunique()
    early = [2012, 2013, 2014, 2015]
    late = [2023, 2024, 2025]
    t = pd.DataFrame({"early_per_year": ny[early].mean(axis=1), "late_per_year": ny[late].mean(axis=1)})
    t["early_share"] = ny[early].sum(axis=1) / tot_located[early].sum()
    t["late_share"] = ny[late].sum(axis=1) / tot_located[late].sum()
    t["share_ratio"] = t.late_share / t.early_share
    t["share_change_pts"] = 100 * (t.late_share - t.early_share)
    t["name"] = names.reindex(t.index)
    t["total"] = ny.sum(axis=1)
    t.sort_values("share_change_pts").to_csv(OUT / "film_nta_change.csv")
    cover["located_permits_by_year"] = {int(k): int(v) for k, v in tot_located.items()}

    # what kind of streets: permit-weighted segment attributes against all lots in the same boroughs
    L = seg[seg.located & (seg.n_lots > 0)]
    attrs = ["yearbuilt_median", "pre1940", "floors_median", "lu01", "lu02", "lu03", "lu04", "lu05", "lu06", "lu11", "histdist"]
    kinds = {"filmed_segments_permit_weighted": {a: float(L[a].mean()) for a in attrs},
             "n_segment_mentions": len(L)}
    ok = p[p.x.notna()]
    lu = ok.landuse.fillna("NA").str.zfill(2)
    yb = ok.yearbuilt.where(ok.yearbuilt > 1700)
    w = L.boro.value_counts(normalize=True)
    base = {}
    for a, series in (("pre1940", (yb < 1940).where(yb.notna())), ("lu01", lu == "01"), ("lu02", lu == "02"), ("lu03", lu == "03"),
                      ("lu04", lu == "04"), ("lu05", lu == "05"), ("lu06", lu == "06"), ("lu11", lu == "11"),
                      ("histdist", ok.histdist.notna())):
        by = series.astype(float).groupby(ok.boro).mean()
        base[a] = float((by.reindex(w.index) * w).sum())
    kinds["all_lots_same_borough_mix"] = base
    kinds["by_period"] = {}
    for lab, yrs in (("2012-2015", early), ("2016-2019", [2016, 2017, 2018, 2019]), ("2023-2025", late)):
        g = L[L.year.isin(yrs)]
        kinds["by_period"][lab] = {a: float(g[a].mean()) for a in attrs} | {"n": len(g)}
    kinds["by_category"] = {c: ({a: float(g[a].mean()) for a in attrs} | {"n": len(g)})
                            for c, g in L.groupby("category") if len(g) > 1500}
    cover["street_kinds"] = kinds

    # points for the map figure: located segments with permit counts by period
    pts = seg[seg.located].groupby(["boro", "street", "c1", "c2"]).agg(
        x=("x", "first"), y=("y", "first"), n=("eventid", "nunique"),
        n_early=("year", lambda v: int((v <= 2015).sum())), n_late=("year", lambda v: int((v >= 2023).sum()))).reset_index()
    pts.to_csv(OUT / "film_segments.csv", index=False)
    (OUT / "film_summary.json").write_text(json.dumps(cover, indent=1, default=float))
    print(json.dumps({k: cover[k] for k in ("shooting_permits", "segment_mentions", "segment_mentions_located", "unique_segments",
                                              "unique_segments_located", "located_share_by_boro")}, indent=1))


if __name__ == "__main__":
    main()
