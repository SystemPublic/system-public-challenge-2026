"""New small businesses in the last two years, by NTA, from four registers.

Restaurants: DOHMH inspection table 43nn-pn8j lists only establishments now operating, with about three
  years of inspections, so a first inspection date is not an opening date for older places. The permit
  number (CAMIS) is issued in sequence; numbers from 50160000 were first inspected no earlier than
  3 September 2024. "New" means CAMIS >= 50160000 with at least one inspection. Registered but not yet
  inspected establishments are counted separately.
Liquor: NYS Liquor Authority active licences. The field "originalissuedate" cannot date openings: 87% of
  the active New York City licences carry a date in 2025 or 2026 (the field follows the latest issue). Only
  the count of active licences is used.
DCWP: premises licences created on or after 13 November 2024, by category.
Dining Out NYC: sidewalk and roadway cafe licences (current programme, all dates).
A business that opened and closed within the window is in none of these.
Output data/derived/explore/shops_nta.csv, shops_summary.json, shops_new_points.csv.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import OUT, RAW, points_to_nta, tract_table, nta_pop

SINCE = "2024-11-13"
CAMIS_NEW = 50160000


def restaurants() -> pd.DataFrame:
    r = pd.read_csv(RAW / "shops" / "restaurants.csv", dtype=str)
    d = pd.read_csv(RAW / "shops" / "restaurant_dates.csv", dtype=str)
    d["dt"] = pd.to_datetime(d.inspection_date)
    first = d[d.dt > "1901-01-01"].groupby("camis").dt.min().rename("first_inspection")
    r = r.drop_duplicates("camis").join(first, on="camis")
    r["lat"] = pd.to_numeric(r.latitude, errors="coerce")
    r["lon"] = pd.to_numeric(r.longitude, errors="coerce")
    r.loc[(r.lat == 0) | (r.lat.isna()), ["lat", "lon"]] = np.nan
    ok = r.lat.notna()
    r["nta"] = None
    r.loc[ok, "nta"] = points_to_nta(r.loc[ok, "lon"], r.loc[ok, "lat"])
    r["camis_n"] = r.camis.astype(int)
    r["inspected"] = r.first_inspection.notna()
    r["new"] = (r.camis_n >= CAMIS_NEW) & r.inspected
    return r


def main():
    names = tract_table().drop_duplicates("nta2020").set_index("nta2020").ntaname
    S = {}
    r = restaurants()
    r.to_csv(OUT / "restaurants_nta.csv", index=False, columns=["camis", "dba", "boro", "zipcode", "cuisine_description", "lat", "lon",
                                                                 "nta", "first_inspection", "inspected", "new"])
    S["restaurants"] = {"active": len(r), "inspected": int(r.inspected.sum()), "new_inspected": int(r.new.sum()),
                        "registered_not_yet_inspected": int((~r.inspected).sum()), "geocoded_share": float(r.nta.notna().mean()),
                        "new_first_inspection_range": [str(r.first_inspection[r.new].min()), str(r.first_inspection[r.new].max())],
                        "new_by_cuisine": r[r.new].cuisine_description.value_counts().head(15).to_dict(),
                        "new_share_by_cuisine": (r[r.inspected].groupby("cuisine_description").new.agg(["mean", "size"])
                                                 .query("size >= 150").sort_values("mean", ascending=False).head(12)
                                                 .rename(columns={"mean": "share_new", "size": "n"}).to_dict("index")),
                        "new_by_boro": r[r.new].boro.value_counts().to_dict(),
                        "new_share_by_boro": r[r.inspected].groupby("boro").new.mean().to_dict()}
    T = pd.DataFrame({"restaurants": r[r.inspected].groupby("nta").size(), "restaurants_new": r[r.new].groupby("nta").size(),
                      "restaurants_pending": r[~r.inspected].groupby("nta").size()})

    lq = pd.read_csv(RAW / "shops" / "liquor.csv", dtype=str)
    xy = lq.georeference.str.extract(r"POINT \(([-\d.]+) ([-\d.]+)\)").astype(float)
    lq["lon"], lq["lat"] = xy[0], xy[1]
    lq["nta"] = None
    ok = lq.lat.notna()
    lq.loc[ok, "nta"] = points_to_nta(lq.loc[ok, "lon"], lq.loc[ok, "lat"])
    S["liquor"] = {"active": len(lq), "geocoded_share": float(lq.nta.notna().mean()),
                   "original_issue_year": lq.originalissuedate.str[:4].value_counts().sort_index().to_dict(),
                   "share_dated_2025_or_2026": float((lq.originalissuedate >= "2025-01-01").mean()),
                   "by_type": lq.description.value_counts().head(8).to_dict()}
    T["liquor"] = lq.groupby("nta").size()

    dc = pd.read_csv(RAW / "shops" / "dcwp_licences.csv", dtype=str)
    dc = dc[dc.license_type == "Premises"].copy()
    dc["lat"] = pd.to_numeric(dc.latitude, errors="coerce")
    dc["lon"] = pd.to_numeric(dc.longitude, errors="coerce")
    dc["new"] = dc.license_creation_date >= SINCE
    ok = dc.lat.notna() & dc.new
    dc["nta"] = None
    dc.loc[ok, "nta"] = points_to_nta(dc.loc[ok, "lon"], dc.loc[ok, "lat"])
    street = ~dc.business_category.isin(["Home Improvement Contractor", "Debt Collection Agency", "Process Serving Agency",
                                         "Third Party Food Delivery Service", "Construction Labor Provider", "Tow Truck Company",
                                         "Pedicab Business", "Horse Drawn Cab Owner", "Sightseeing Bus", "Employment Agency"])
    S["dcwp"] = {"premises_licences": len(dc), "new": int(dc.new.sum()), "new_by_category": dc[dc.new].business_category.value_counts().head(14).to_dict(),
                 "new_storefront_categories": int((dc.new & street).sum()), "new_geocoded_share": float(dc[dc.new].nta.notna().mean())}
    T["dcwp_new_storefront"] = dc[dc.new & street].groupby("nta").size()

    do = pd.read_csv(RAW / "shops" / "dining_out.csv", dtype=str)
    S["dining_out"] = {"rows": len(do), "status": do.license_status.value_counts().to_dict(), "type": do.license_type.value_counts().to_dict()}
    T["dining_out"] = do[do.license_status == "Issued"].groupby("nta2020").size()

    T = T.fillna(0).astype(int)
    T = T[T.index.notna()]
    T["new_share"] = T.restaurants_new / T.restaurants.replace(0, np.nan)
    T["name"] = names.reindex(T.index)
    p = nta_pop().set_index("nta")["pop"]
    T["pop"] = p.reindex(T.index)
    T["new_per_10k"] = 1e4 * T.restaurants_new / T["pop"].replace(0, np.nan)
    T.sort_values("restaurants_new", ascending=False).to_csv(OUT / "shops_nta.csv")
    city_share = T.restaurants_new.sum() / T.restaurants.sum()
    S["city_new_share"] = float(city_share)
    big = T[T.restaurants >= 60]
    S["top_by_count"] = T.sort_values("restaurants_new", ascending=False).head(15)[["name", "restaurants_new", "restaurants", "new_share"]].to_dict("records")
    S["top_by_share"] = big.sort_values("new_share", ascending=False).head(15)[["name", "restaurants_new", "restaurants", "new_share"]].to_dict("records")
    S["bottom_by_share"] = big.sort_values("new_share").head(10)[["name", "restaurants_new", "restaurants", "new_share"]].to_dict("records")
    (OUT / "shops_summary.json").write_text(json.dumps(S, indent=1, default=float))
    r[r.new & r.lat.notna()][["lat", "lon", "cuisine_description"]].round(5).to_csv(OUT / "shops_new_points.csv", index=False)
    print(json.dumps(S, indent=1, default=float))


if __name__ == "__main__":
    main()
