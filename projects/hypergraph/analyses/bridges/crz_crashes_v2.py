"""Endpoint test for bridge-crz-injury-crashes-v2 (registered plan in claims/registered/).

Injury crashes from h9gi-nx95 in the MTA CBD geofence (largest polygon) against
Manhattan north of 60th Street, 2025 against 2022-2024, with the registered bias
bounds for the 2025 change in geocoding and the stable-coverage restrictions.
Outputs: data/derived/bridges/crz_crashes_v2_monthly.csv, crz_crashes_v2_results.json
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
from shapely import contains_xy, make_valid
from shapely.geometry import shape
from shapely.ops import unary_union

from analyses.bridges.common import DER, ROOT
from analyses.bridges.crz_crashes import did_ols, did_poisson, zone_polygons
from concord import socrata
from concord.claims import endpoint_stance

D0, D1 = "2022-01-01", "2026-08-31T23:59:59"
INJ = "(number_of_persons_injured > 0 or number_of_persons_killed > 0)"
BOX = "latitude between 40.68 and 40.89 and longitude between -74.03 and -73.90"
NOCOORD = "sum(case(latitude is null or latitude = 0, 1, true, 0))"
CLS = ("case(on_street_name is not null and cross_street_name is not null, 'intersection', "
       "off_street_name is not null, 'address', true, 'other')")
K = math.radians(29)
# cached v1 counts (h9gi-nx95-b14f...): injury crashes coded MANHATTAN, and those without coordinates
MANH_CODED = {"pre": (233 + 104 + 104, 4353 + 4640 + 4900), "2025": (266, 6060)}


def u(lat, lon):
    """Distance along the Manhattan avenue axis (km), as in analyses/mobility/crz_air.py."""
    return (lon + 73.97) * 84.2 * math.sin(K) + (lat - 40.76) * 111.0 * math.cos(K)


U60, U96 = u(40.7648, -73.9727), u(40.7858, -73.9578)


def manhattan():
    g = json.loads((ROOT / "data/raw/ehdp/UHF42.geojson").read_text())
    man = unary_union([make_valid(shape(f["geometry"])) for f in g["features"] if f["properties"]["BOROUGH"] == "Manhattan"])
    oth = unary_union([make_valid(shape(f["geometry"])) for f in g["features"]
                       if f["properties"]["BOROUGH"] not in ("Manhattan", "N/A")])
    return man.buffer(0.0005), oth


def fetch_rows():
    rows, src = socrata.query_all(
        "h9gi-nx95", order="collision_id",
        select="collision_id, crash_date, latitude, longitude, borough, on_street_name, cross_street_name, off_street_name, "
               "number_of_persons_injured, number_of_persons_killed",
        where=f"crash_date between '{D0}' and '{D1}' and {INJ} and {BOX}")
    return pd.DataFrame(rows), src


def coverage_by_class():
    rows, src = socrata.query("h9gi-nx95", select=f"date_extract_y(crash_date) as y, {CLS} as cls, count(*) as n, {NOCOORD} as nocoord",
                              where=f"crash_date between '2022-01-01' and '2025-12-31T23:59:59' and {INJ}",
                              group="y, cls", order="y, cls")
    d = pd.DataFrame(rows)
    d[["y", "n", "nocoord"]] = d[["y", "n", "nocoord"]].astype(float)
    return d, src


def coverage_by_month():
    rows, src = socrata.query("h9gi-nx95", select=f"date_trunc_ym(crash_date) as m, count(*) as n, {NOCOORD} as nocoord",
                              where=f"crash_date between '2022-01-01' and '2025-12-31T23:59:59' and {INJ}",
                              group="m", order="m")
    d = pd.DataFrame(rows)
    d["month"] = pd.to_datetime(d["m"])
    d[["n", "nocoord"]] = d[["n", "nocoord"]].astype(float)
    d["coverage"] = 1 - d["nocoord"] / d["n"]
    return d[["month", "n", "nocoord", "coverage"]], src


def assign(d, main_poly, union_poly):
    for c in ("latitude", "longitude", "number_of_persons_injured", "number_of_persons_killed"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d = d[(d.latitude != 0) & (d.longitude != 0)].copy()
    man, oth = manhattan()
    x, y = d["longitude"].values, d["latitude"].values
    in_zone = contains_xy(main_poly, x, y)
    in_geof = contains_xy(union_poly, x, y)
    in_man = contains_xy(man, x, y) & ~contains_xy(oth, x, y)
    uu = u(d["latitude"].values, d["longitude"].values)
    north = in_man & ~in_geof & (uu >= U60)
    d["area"] = np.where(in_zone, "zone", np.where(north, "north", "other"))
    d["band"] = north & (uu < U96)
    d["month"] = pd.to_datetime(d["crash_date"]).dt.to_period("M").dt.to_timestamp()
    def present(c):
        if c not in d:
            return pd.Series(False, index=d.index)
        return d[c].notna() & (d[c].astype(str).str.strip() != "")
    on, cr, off = present("on_street_name"), present("cross_street_name"), present("off_street_name")
    d["cls"] = np.where(on & cr, "intersection", np.where(off, "address", "other"))
    d["killed"] = d["number_of_persons_killed"]
    return d


def monthly(d, comp_mask, months):
    z = d[d.area == "zone"].groupby("month").size().reindex(months, fill_value=0)
    n = d[comp_mask].groupby("month").size().reindex(months, fill_value=0)
    return pd.DataFrame({"zone": z, "comp": n})


def long(m, start="2022-01-01", end="2025-12-01", keep_pre=None):
    out = []
    for area, col in (("zone", "zone"), ("north", "comp")):
        s = m[col]
        out.append(pd.DataFrame({"month": s.index, "v": s.values, "area": area}))
    d = pd.concat(out)
    d = d[(d["month"] >= start) & (d["month"] <= end)].copy()
    if keep_pre is not None:
        d = d[(d["month"] >= "2025-01-01") | d["month"].isin(keep_pre)]
    d["calm"] = d["month"].dt.month
    d["year"] = d["month"].dt.year
    d["treat"] = (d["area"] == "zone").astype(int)
    return d.sort_values(["area", "month"])


def zs(b, se, mu, sig):
    zc = (b - mu) / math.sqrt(se * se + sig * sig)
    zn = b / se
    return {"b_log": b, "pct": 100 * (math.exp(b) - 1), "lo": 100 * (math.exp(b - 1.96 * se) - 1),
            "hi": 100 * (math.exp(b + 1.96 * se) - 1), "z_chain": zc, "z_null": zn, "D": zn * zn - zc * zc,
            "compatible": abs(zc) < 1.96, "discriminates": zn * zn - zc * zc >= 4}


def condition(r):
    if r["compatible"] and r["discriminates"]:
        return "bridged"
    if not r["compatible"]:
        return "contested_" + ("above" if r["z_chain"] > 0 else "below")
    return "unsettled"


def main():
    comp = json.loads((DER / "composed_predictions_v2.json").read_text())
    P, S = comp["primary_independent"]["composed_injury_crashes_pct"], comp["sensitivity_correlated"]["composed_injury_crashes_pct"]
    V1 = json.loads((DER / "composed_predictions.json").read_text())["bridge-crz-injury-crashes"]["composed_injury_crashes_pct"]
    main_poly, union_poly, src_poly = zone_polygons()
    raw, src_rows = fetch_rows()
    cls, src_cls = coverage_by_class()
    mon, src_mon = coverage_by_month()
    d = assign(raw, main_poly, union_poly)
    months = pd.date_range("2022-01-01", "2026-08-01", freq="MS")
    res = {}

    m = monthly(d, d.area == "north", months)
    ann = m.groupby(m.index.year).sum()
    res["annual_injury_crashes"] = {int(k): {"zone": int(v.zone), "north": int(v.comp)} for k, v in ann.iterrows()}
    if (ann.loc[2022:2025, "comp"] < 1000).any():
        res["no_test"] = "north area below 1,000 injury crashes in a year"

    lf = long(m)
    p = did_ols(lf, "2025-01-01")
    res["primary"] = {**p, **zs(p["log"], p["se"], P["mean_log"], P["sd_log"])}
    pl = did_ols(lf[lf["month"] < "2025-01-01"], "2024-01-01")
    res["placebo_2024"] = {**pl, "includes_zero": pl["lo"] < 0 < pl["hi"]}

    # bias bounds
    pre = d[(d.month < "2025-01-01") & (d.month >= "2022-01-01")]
    nz, nn = (pre.area == "zone").sum(), (pre.area == "north").sum()
    w = nz / (nz + nn)
    tot = cls.groupby("y")[["n", "nocoord"]].sum()
    miss_pre = tot.loc[2022:2024, "nocoord"].sum() / tot.loc[2022:2024, "n"].sum()
    miss_25 = tot.loc[2025, "nocoord"] / tot.loc[2025, "n"]
    Dn = miss_pre - miss_25
    e = MANH_CODED["2025"][0] / MANH_CODED["2025"][1] - MANH_CODED["pre"][0] / MANH_CODED["pre"][1]
    rN1 = Dn / (1 + w); rZ1 = 2 * rN1
    rZ2 = Dn / (2 - w); rN2 = 2 * rZ2
    bias = {"B0": 0.0,
            "B1": math.log(1 + rZ1) - math.log(1 + rN1),
            "B2": math.log(1 + rZ2) - math.log(1 + rN2),
            "B3": math.log(1 - e / w),
            "B4": -math.log(1 - e / (1 - w)),
            "extreme_all_in_zone": math.log(1 + Dn / w),
            "extreme_all_in_north": -math.log(1 + Dn / (1 - w))}
    bias["B_up"] = bias["B2"] + bias["B3"]
    bias["B_down"] = bias["B1"] + bias["B4"]
    res["bias_inputs"] = {"w_zone_share_2022_24": w, "D_new_citywide": Dn, "missing_share_2022_24": miss_pre, "missing_share_2025": miss_25,
                          "e_manhattan_coded_rise": e}
    res["bias_log"] = bias
    res["corrected"] = {k: zs(p["log"] - b, p["se"], P["mean_log"], P["sd_log"]) for k, b in bias.items()}
    for k in res["corrected"]:
        res["corrected"][k]["condition"] = condition(res["corrected"][k])

    # registered decision
    conds = [res["corrected"][k]["condition"] for k in ("B0", "B_up", "B_down")]
    if "no_test" in res:
        verdict = "no_test"
    elif not res["placebo_2024"]["includes_zero"]:
        verdict = "unsettled"
    elif all(c == "bridged" for c in conds):
        verdict = "bridged"
    elif all(c.startswith("contested") for c in conds) and len(set(conds)) == 1:
        verdict = "contested"
    else:
        verdict = "unsettled"
    res["verdict_by_rule"] = verdict
    res["conditions"] = dict(zip(("B0", "B_up", "B_down"), conds))
    res["stance"] = endpoint_stance(res["primary"]["z_chain"], res["primary"]["z_null"])

    # secondary
    cl = cls.copy()
    cl["cov"] = 1 - cl["nocoord"] / cl["n"]
    piv = cl.pivot(index="cls", columns="y", values="cov")
    shares = cl.pivot(index="cls", columns="y", values="n")
    res["coverage_by_class"] = {c: {"coverage": {int(y): float(piv.loc[c, y]) for y in piv.columns},
                                    "n": {int(y): int(shares.loc[c, y]) for y in shares.columns},
                                    "range_pp": float(100 * (piv.loc[c].max() - piv.loc[c].min()))} for c in piv.index}
    stable = [c for c in piv.index if 100 * (piv.loc[c].max() - piv.loc[c].min()) < 2]
    res["stable_classes"] = stable
    if stable:
        ds = d[d.cls.isin(stable)]
        ms = monthly(ds, ds.area == "north", months)
        r = did_ols(long(ms), "2025-01-01")
        res["stable_class_restriction"] = {**r, **zs(r["log"], r["se"], P["mean_log"], P["sd_log"]),
                                           "n_rows_share": float(len(ds) / len(d))}
    else:
        res["stable_class_restriction"] = "not run: no class has coverage varying by less than 2 points across 2022-2025"
    cov25 = mon[mon.month >= "2025-01-01"]["coverage"].mean()
    keep = mon[(mon.month < "2025-01-01") & ((mon.coverage - cov25).abs() < 0.02)]["month"]
    res["coverage_2025_mean"] = float(cov25)
    res["stable_pre_months"] = [str(x.date()) for x in keep]
    if len(keep) >= 12:
        r = did_ols(long(m, keep_pre=set(keep)), "2025-01-01")
        res["stable_month_restriction"] = {**r, **zs(r["log"], r["se"], P["mean_log"], P["sd_log"])}
    else:
        res["stable_month_restriction"] = f"not run: {len(keep)} pre-period months within 2 points of the 2025 mean coverage (12 needed)"

    mb = monthly(d, d.band, months)
    r = did_ols(long(mb), "2025-01-01")
    res["secondary_area_60_96"] = {**r, **zs(r["log"], r["se"], P["mean_log"], P["sd_log"])}
    res["secondary_area_60_96_placebo_2024"] = did_ols(long(mb)[lambda x: x["month"] < "2025-01-01"], "2024-01-01")
    r = did_poisson(lf, "2025-01-01")
    res["poisson_area_by_month"] = {**r, **zs(r["log"], r["se"], P["mean_log"], P["sd_log"])}
    res["correlated_composition"] = zs(p["log"], p["se"], S["mean_log"], S["sd_log"])
    res["v1_composition"] = zs(p["log"], p["se"], V1["mean_log"], V1["sd_log"])
    r = did_ols(long(m, end="2026-08-01"), "2025-01-01")
    res["through_aug_2026"] = {**r, **zs(r["log"], r["se"], P["mean_log"], P["sd_log"])}
    res["rows"] = {"fetched": int(len(raw)), "geocoded": int(len(d)), "zone": int((d.area == "zone").sum()),
                   "north": int((d.area == "north").sum()), "band_60_96": int(d.band.sum())}

    out = pd.concat({"zone": m["zone"], "north": m["comp"], "band_60_96": mb["comp"]}, axis=1)
    out.index.name = "month"
    out.to_csv(DER / "crz_crashes_v2_monthly.csv")
    mon.to_csv(DER / "crz_crashes_v2_coverage_monthly.csv", index=False)
    (DER / "crz_crashes_v2_results.json").write_text(json.dumps(
        {"results": res, "composed": P, "composed_correlated": S, "sources": [src_poly, src_rows, src_cls, src_mon]},
        indent=1, default=float))
    print(json.dumps(res, indent=1, default=lambda x: round(float(x), 4)))


if __name__ == "__main__":
    main()
