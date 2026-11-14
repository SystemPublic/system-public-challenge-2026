"""Burden and reach for each lever from New York City data (descriptive, not a test).

Burden: the size of the outcome a lever acts on, per year, and how concentrated it is: the share held by the tenth
of areas (community districts, ZIP codes or NTAs) with the most. Reach: how many places or people are eligible.
Writes data/derived/levers/city_metrics.json and shootings_2023_2025.csv (points, used by the lot test as well).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

OUT = ROOT / "data" / "derived" / "levers"
EHDP = Path.home() / "opt" / "nyc-concordance" / "ehdp"
M: dict = {}
SRC: dict = {}


def q(name, ds, **soql):
    if "group" in soql or "count(" in soql.get("select", ""):
        rows, src = socrata.query(ds, limit=50000, **soql)
    else:
        rows, src = socrata.query_all(ds, **soql)
    SRC[name] = src
    return pd.DataFrame(rows)


def top_decile_share(v) -> float:
    v = np.sort(np.asarray(v, float))[::-1]
    v = v[np.isfinite(v)]
    k = max(1, int(round(len(v) / 10)))
    return float(v[:k].sum() / v.sum()) if v.sum() > 0 else float("nan")


def put(key, value, unit, source, distribution=None, unit_of_area=None, note=""):
    M[key] = {"value": value, "unit": unit, "source": source, "top_decile_share": distribution,
              "areas": unit_of_area, "note": note}


def main():
    # shootings, 2023-2025
    sh = q("shootings", "5ucz-vwe8", select="incident_key,occur_date,occur_time,boro,precinct,latitude,longitude",
           where="occur_date >= '2023-01-01T00:00:00' and occur_date < '2026-01-01T00:00:00'")
    sh.to_csv(OUT / "shootings_2023_2025.csv", index=False)
    inc = sh.drop_duplicates("incident_key")
    pc = inc.groupby("precinct").size()
    put("shootings", round(len(inc) / 3, 1), "shooting incidents a year, 2023-2025", "5ucz-vwe8",
        top_decile_share(pc), "77 police precincts")

    # collisions 2023-2025 by ZIP
    co = q("collisions", "h9gi-nx95",
           select="zip_code,sum(number_of_pedestrians_injured) as pi,sum(number_of_pedestrians_killed) as pk,"
                  "sum(number_of_cyclist_injured) as ci,sum(number_of_cyclist_killed) as ck,"
                  "sum(number_of_persons_injured) as ai,sum(number_of_persons_killed) as ak",
           where="crash_date >= '2023-01-01T00:00:00' and crash_date < '2026-01-01T00:00:00'", group="zip_code")
    for c in ("pi", "pk", "ci", "ck", "ai", "ak"):
        co[c] = pd.to_numeric(co[c], errors="coerce").fillna(0)
    z = co[co.zip_code.notna()]
    put("ped_injuries", round((co.pi.sum() + co.pk.sum()) / 3), "pedestrians injured or killed a year, 2023-2025",
        "h9gi-nx95", top_decile_share(z.pi + z.pk), "ZIP codes (crashes with a ZIP)",
        "About a third of crashes have no ZIP code; the city total includes them.")
    put("cyclist_injuries", round((co.ci.sum() + co.ck.sum()) / 3), "cyclists injured or killed a year, 2023-2025",
        "h9gi-nx95", top_decile_share(z.ci + z.ck), "ZIP codes")
    put("traffic_deaths", round(co.ak.sum() / 3, 1), "people killed in crashes a year, 2023-2025", "h9gi-nx95",
        top_decile_share(z.ak), "ZIP codes")

    # asthma ED visits (EHDP), latest year, by community district
    tp = {t["TimePeriodID"]: t for t in json.load(open(EHDP / "TimePeriods.json"))}
    tot, dist, yr = 0.0, None, None
    for ind, mid in (("2048", 459), ("2379", 1195), ("2380", 1197)):
        d = pd.DataFrame(json.load(open(EHDP / f"{ind}.json")))
        d = d[(d.MeasureID == mid)]
        d = d[d.TimePeriodID.map(lambda i: tp.get(i, {}).get("TimeType") == "year")]
        last = d.TimePeriodID.map(lambda i: int(tp[i]["TimePeriod"])).max()
        d = d[d.TimePeriodID.map(lambda i: int(tp[i]["TimePeriod"])) == last]
        yr = last
        tot += float(d[d.GeoType == "Citywide"].Value.sum())
        cd = d[d.GeoType == "CD"].set_index("GeoID").Value.astype(float)
        dist = cd if dist is None else dist.add(cd, fill_value=0)
    put("asthma_ed", tot, f"asthma emergency department visits, all ages, {yr}",
        "NYC Environment and Health Data Portal, indicators 2048, 2379, 2380", top_decile_share(dist), "59 community districts")

    # heat: deaths and ED visits (EHDP, already in repo)
    he = pd.read_csv(ROOT / "data/derived/heat/ehdp_yearly.csv")
    rec = he.dropna(subset=["heat_ed_visits"]).tail(5)
    put("heat_ed", round(float(rec.heat_ed_visits.mean())), f"heat-illness ED visits a year, {int(rec.year.min())}-{int(rec.year.max())}",
        "data/derived/heat/ehdp_yearly.csv (EHDP)")
    rd = he.dropna(subset=["heat_deaths"]).tail(5)
    put("heat_deaths", round(float(rd.heat_deaths.mean()), 1), f"heat-stress deaths a year, {int(rd.year.min())}-{int(rd.year.max())}",
        "data/derived/heat/ehdp_yearly.csv (EHDP)", note="Heat-stress deaths only; heat-exacerbated deaths are several times more.")

    # reach: households without air conditioning (EHDP NTA percentages; weighted by NTA population from tracts)
    br = pd.read_csv(ROOT / "data/derived/heat/bridge_nta.csv")
    acs = pd.read_csv(ROOT / "data/derived/neighbourhood/tracts_acs.csv") if (ROOT / "data/derived/neighbourhood/tracts_acs.csv").exists() else None
    no_ac = 100 - br.PCT_HOUSEHOLDS_AC
    put("no_ac_share", round(float(no_ac.mean()), 1), "per cent of households without air conditioning (unweighted mean of NTAs)",
        "data/derived/heat/bridge_nta.csv (EHDP, NTA 2010)", top_decile_share(no_ac), "NTAs (2010)")

    # HPD: buildings with open class C violations; open mold; open lead paint
    hp = q("hpd_open_c", "wvxf-dwi5", select="nta,count(distinct buildingid) as b",
           where="violationstatus='Open' and class='C'", group="nta")
    hp["b"] = pd.to_numeric(hp.b)
    tot_c = q("hpd_open_c_total", "wvxf-dwi5", select="count(distinct buildingid) as b",
              where="violationstatus='Open' and class='C'")
    put("hpd_open_c_buildings", int(tot_c.b.iloc[0]), "buildings with an open class C (immediately hazardous) HPD violation",
        "wvxf-dwi5", top_decile_share(hp.b), "NTAs")
    mo = q("hpd_open_mold", "wvxf-dwi5", select="count(distinct buildingid) as b",
           where="violationstatus='Open' and upper(novdescription) like '%MOLD%'")
    put("hpd_open_mold_buildings", int(mo.b.iloc[0]), "buildings with an open HPD mold violation", "wvxf-dwi5")
    ld = q("hpd_open_lead", "wvxf-dwi5", select="count(distinct buildingid) as b",
           where="violationstatus='Open' and upper(novdescription) like '%LEAD%'")
    put("hpd_open_lead_buildings", int(ld.b.iloc[0]), "buildings with an open HPD lead-paint violation", "wvxf-dwi5")
    ht = q("hpd_open_heat", "wvxf-dwi5", select="count(distinct buildingid) as b",
           where="violationstatus='Open' and upper(novdescription) like '%HEAT%'")
    put("hpd_open_heat_buildings", int(ht.b.iloc[0]), "buildings with an open HPD violation mentioning heat", "wvxf-dwi5")

    # vacate orders still in force (abandoned or unsafe buildings)
    va = q("vacate", "tb8q-a3ar", select="nta,count(*) as n", where="actual_rescind_date is null", group="nta")
    va["n"] = pd.to_numeric(va.n)
    put("vacate_orders_active", int(va.n.sum()), "HPD vacate orders not rescinded", "tb8q-a3ar", top_decile_share(va.n), "NTAs")

    # speed reducers: requests and installations
    sr = q("speed_reducers", "9n6h-pt9g", select="projectstatus,count(*) as n", group="projectstatus")
    sr["n"] = pd.to_numeric(sr.n)
    put("speed_reducer_requests", {r.projectstatus: int(r.n) for r in sr.itertuples()},
        "speed reducer requests by status (all years)", "9n6h-pt9g")

    # street trees 2015: dead and stumps (planting sites that need a tree)
    tr = q("trees2015", "uvpi-gqnh", select="status,count(*) as n", group="status")
    tr["n"] = pd.to_numeric(tr.n)
    put("tree_status_2015", {r.status: int(r.n) for r in tr.itertuples()}, "street trees by status, 2015 census", "uvpi-gqnh")

    # GreenThumb gardens
    gt = q("greenthumb", "p78i-pat6", select="status,count(*) as n", group="status")
    gt["n"] = pd.to_numeric(gt.n)
    put("greenthumb_gardens", {str(r.status): int(r.n) for r in gt.itertuples()}, "GreenThumb gardens by status", "p78i-pat6")

    # 311 street light complaints 2025
    sl = q("streetlight311", "erm2-nwe9", select="count(*) as n",
           where="complaint_type='Street Light Condition' and created_date >= '2025-01-01T00:00:00' and created_date < '2026-01-01T00:00:00'")
    put("streetlight_complaints_2025", int(sl.n.iloc[0]), "311 street light condition complaints, 2025", "erm2-nwe9")

    (OUT / "city_metrics.json").write_text(json.dumps({"metrics": M, "sources": SRC}, indent=1, default=str))
    for k, v in M.items():
        print(k, v["value"], "|", v["unit"], "| top decile", v["top_decile_share"])


if __name__ == "__main__":
    main()
