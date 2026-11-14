"""Endpoint test for bridge-crz-injury-crashes (registered plan in claims/registered/).

Crashes from h9gi-nx95 inside the MTA CBD geofence polygon (srxy-5nxn, largest
polygon) against the rest of the city, 2025 against 2022-2024.
Outputs: data/derived/bridges/crz_crashes_monthly.csv, crz_crashes_results.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from shapely import contains_xy
from shapely.geometry import shape
from shapely.ops import unary_union

from analyses.bridges.common import DER
from analyses.mobility.common import nys
from concord import socrata

D0, D1 = "2022-01-01", "2026-08-31T23:59:59"
BBOX = "latitude between 40.69 and 40.78 and longitude between -74.03 and -73.95"
CITY = "latitude between 40.45 and 40.95 and longitude between -74.30 and -73.65"
OUTCOMES = {
    "injury_crashes": "sum(case(number_of_persons_injured > 0 or number_of_persons_killed > 0, 1, true, 0))",
    "crashes": "count(*)",
    "persons_injured": "sum(number_of_persons_injured)",
    "persons_killed": "sum(number_of_persons_killed)",
    "ped_cyc_injured": "sum(number_of_pedestrians_injured + number_of_cyclist_injured)",
}


def zone_polygons():
    rows, src = nys("srxy-5nxn", limit=5000)
    gs = [shape(r["polygon"]) for r in rows]
    gs.sort(key=lambda g: -g.area)
    return gs[0], unary_union(gs), src


def zone_monthly(main, union):
    rows, src = socrata.query_all(
        "h9gi-nx95", order="collision_id",
        select="collision_id, crash_date, latitude, longitude, number_of_persons_injured, number_of_persons_killed, "
               "number_of_pedestrians_injured, number_of_cyclist_injured",
        where=f"crash_date between '{D0}' and '{D1}' and {BBOX}")
    d = pd.DataFrame(rows)
    for c in d.columns:
        if c.startswith("number_") or c in ("latitude", "longitude"):
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["month"] = pd.to_datetime(d["crash_date"]).dt.to_period("M").dt.to_timestamp()
    d["in_main"] = contains_xy(main, d["longitude"].values, d["latitude"].values)
    d["in_union"] = contains_xy(union, d["longitude"].values, d["latitude"].values)
    d["injury_crashes"] = ((d.number_of_persons_injured > 0) | (d.number_of_persons_killed > 0)).astype(int)
    d["crashes"] = 1
    d["persons_injured"] = d.number_of_persons_injured
    d["persons_killed"] = d.number_of_persons_killed
    d["ped_cyc_injured"] = d.number_of_pedestrians_injured + d.number_of_cyclist_injured
    cols = list(OUTCOMES)
    zm = d[d.in_main].groupby("month")[cols].sum()
    zu = d[d.in_union].groupby("month")[cols].sum()
    return zm, zu, src


def city_monthly():
    sel = "date_trunc_ym(crash_date) as m, " + ", ".join(f"{v} as {k}" for k, v in OUTCOMES.items())
    rows, src = socrata.query("h9gi-nx95", select=sel, where=f"crash_date between '{D0}' and '{D1}' and {CITY}",
                              group="m", order="m")
    c = pd.DataFrame(rows)
    c["month"] = pd.to_datetime(c["m"])
    c = c.set_index("month")[list(OUTCOMES)].astype(float)
    return c, src


def missing_coords():
    rows, src = socrata.query("h9gi-nx95", select="date_extract_y(crash_date) as y, count(*) as n, "
                              "sum(case(latitude is null or latitude = 0, 1, true, 0)) as nocoord, "
                              "sum(case(borough = 'MANHATTAN', 1, true, 0)) as manh, "
                              "sum(case(borough = 'MANHATTAN' and (latitude is null or latitude = 0), 1, true, 0)) as manh_nocoord",
                              where=f"crash_date between '{D0}' and '{D1}'", group="y", order="y")
    return pd.DataFrame(rows).astype(float), src


def long_frame(zone, city, outcome, start="2022-01-01", end="2025-12-01"):
    z = zone[outcome].rename("v").to_frame().assign(area="zone")
    r = (city[outcome] - zone[outcome].reindex(city.index).fillna(0)).rename("v").to_frame().assign(area="rest")
    d = pd.concat([z, r]).reset_index().rename(columns={"index": "month"})
    d = d[(d["month"] >= start) & (d["month"] <= end)].copy()
    d["calm"] = d["month"].dt.month
    d["year"] = d["month"].dt.year
    d["treat"] = (d["area"] == "zone").astype(int)
    return d.sort_values(["area", "month"])


def did_ols(d, start):
    d = d.copy()
    d["post"] = (d["month"] >= start).astype(int)
    d["y"] = np.log(d["v"].clip(lower=0.5))
    m = smf.ols("y ~ C(area) + C(calm) + C(year) + treat:post", data=d).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    b, se = float(m.params["treat:post"]), float(m.bse["treat:post"])
    return {"log": b, "se": se, "pct": 100 * (np.exp(b) - 1), "lo": 100 * (np.exp(b - 1.96 * se) - 1),
            "hi": 100 * (np.exp(b + 1.96 * se) - 1), "n": int(m.nobs)}


def did_poisson(d, start):
    d = d.copy()
    d["post"] = (d["month"] >= start).astype(int)
    m = smf.glm("v ~ C(area) * C(calm) + C(area) + C(year) + treat:post", data=d,
                family=sm.families.Poisson()).fit(scale="X2")
    b, se = float(m.params["treat:post"]), float(m.bse["treat:post"])
    return {"log": b, "se": se, "pct": 100 * (np.exp(b) - 1), "lo": 100 * (np.exp(b - 1.96 * se) - 1),
            "hi": 100 * (np.exp(b + 1.96 * se) - 1), "n": int(m.nobs)}


def compat(obs, pred_mean_log, pred_sd_log):
    D = obs["log"] - pred_mean_log
    se = float(np.sqrt(obs["se"] ** 2 + pred_sd_log ** 2))
    return {"D": D, "se": se, "z": D / se, "compatible": bool(abs(D / se) < 1.96)}


def main():
    main_poly, union_poly, src_poly = zone_polygons()
    zm, zu, src_z = zone_monthly(main_poly, union_poly)
    city, src_c = city_monthly()
    miss, src_m = missing_coords()
    comp = json.loads((DER / "composed_predictions.json").read_text())["bridge-crz-injury-crashes"]["composed_injury_crashes_pct"]

    res = {}
    d = long_frame(zm, city, "injury_crashes")
    res["primary_injury_crashes"] = did_ols(d, "2025-01-01")
    res["placebo_2024"] = did_ols(d[d["month"] < "2025-01-01"], "2024-01-01")
    res["compatibility"] = compat(res["primary_injury_crashes"], comp["mean_log"], comp["sd_log"])
    res["poisson_injury_crashes"] = did_poisson(d, "2025-01-01")
    for o in ("persons_injured", "ped_cyc_injured", "crashes"):
        dd = long_frame(zm, city, o)
        res[f"{o}"] = did_ols(dd, "2025-01-01")
        res[f"{o}_placebo_2024"] = did_ols(dd[dd["month"] < "2025-01-01"], "2024-01-01")
    res["persons_killed_poisson"] = did_poisson(long_frame(zm, city, "persons_killed"), "2025-01-01")
    res["with_highways"] = did_ols(long_frame(zu, city, "injury_crashes"), "2025-01-01")
    res["through_aug_2026"] = did_ols(long_frame(zm, city, "injury_crashes", end="2026-08-01"), "2025-01-01")

    ann = zm.groupby(zm.index.year).sum().join(city.groupby(city.index.year).sum(), rsuffix="_city")
    res["annual"] = ann.to_dict(orient="index")
    res["missing_coordinates_by_year"] = miss.to_dict(orient="records")

    out = pd.concat({"zone": zm, "zone_with_highways": zu, "city": city}, axis=1)
    out.to_csv(DER / "crz_crashes_monthly.csv")
    (DER / "crz_crashes_results.json").write_text(json.dumps(
        {"results": res, "composed": comp, "sources": [src_poly, src_z, src_c, src_m]}, indent=1, default=float))
    for k, v in res.items():
        if k not in ("annual", "missing_coordinates_by_year"):
            print(k, {a: round(b, 3) if isinstance(b, float) else b for a, b in v.items()})
    print(pd.DataFrame(res["annual"]).T[["injury_crashes", "persons_killed", "injury_crashes_city"]])
    print(miss)


if __name__ == "__main__":
    main()
