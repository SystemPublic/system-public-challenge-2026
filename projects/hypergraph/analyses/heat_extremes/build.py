"""Daily aggravated-assault counts and maximum temperature for eight US cities.

Each city's counts come from its official open-data portal, counted by date of occurrence
(Philadelphia: dispatch date, the only date published). Temperature is GHCN-Daily TMAX at one
long-running station per city. Shootings are added for New York, Chicago and Philadelphia.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.heat_extremes.build
Writes data/derived/heat_extremes/daily_<city>.csv and sources.json.
Large raw files are kept outside the repository in ~/opt/nyc-concordance/heat_extremes/.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

import concord.socrata as soc
from analyses.heat.common import holidays
from concord import noaa

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "heat_extremes"
RAW = Path.home() / "opt" / "nyc-concordance" / "heat_extremes"
UA = {"User-Agent": "research-script/1.0"}
END = "2026-08-31"

CITIES = {
    # key: (label, station, start, end)
    "phoenix": ("Phoenix", "USW00023183", "2015-11-01", "2025-11-30"),
    "tucson": ("Tucson", "USW00023160", "2018-01-01", END),
    "dallas": ("Dallas", "USW00013960", "2017-01-01", END),
    "austin": ("Austin", "USW00013958", "2003-01-01", END),
    "los_angeles": ("Los Angeles", "USW00093134", "2010-01-01", "2023-12-31"),
    "philadelphia": ("Philadelphia", "USW00013739", "2006-01-01", END),
    "chicago": ("Chicago", "USW00014819", "2006-01-01", END),
    "new_york": ("New York", "USW00094728", "2006-01-01", "2025-12-31"),
}
SRC: dict[str, list] = {}


def _soc(domain, dataset, **q):
    old = soc.DOMAIN
    soc.DOMAIN = domain
    try:
        rows, src = soc.query_all(dataset, **q)
    finally:
        soc.DOMAIN = old
    src["domain"] = domain
    return rows, src


def _get(url, params, tries=6):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=300)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def _series(rows, d="d", n="n"):
    s = pd.Series({pd.Timestamp(str(r[d])[:10]): int(r[n]) for r in rows if r.get(d)})
    return s.groupby(level=0).sum().sort_index()


def soc_daily(city, domain, dataset, datefield, where, start, end, count="count(*)"):
    w = f"{datefield} between '{start}T00:00:00' and '{end}T23:59:59' AND ({where})"
    rows, src = _soc(domain, dataset, select=f"date_trunc_ymd({datefield}) as d, {count} as n", where=w, group="d", order="d")
    SRC.setdefault(city, []).append(src)
    return _series(rows)


def los_angeles(start, end):
    w = "crm_cd in ('230','231','235','236')"
    a = soc_daily("los_angeles", "https://data.lacity.org", "63jg-8b9z", "date_occ", w, start, "2019-12-31")
    b = soc_daily("los_angeles", "https://data.lacity.org", "2nrs-mtv8", "date_occ", w, "2020-01-01", end)
    return a.add(b, fill_value=0)


def philadelphia(start, end, shootings=False):
    f = RAW / "philadelphia" / ("shootings.json" if shootings else "aggassault.json")
    f.parent.mkdir(parents=True, exist_ok=True)
    if shootings:
        q = f"select date_::date as d, count(*) as n from shootings where date_ between '{start}' and '{end}' group by 1 order by 1"
    else:
        q = ("select dispatch_date as d, count(*) as n from incidents_part1_part2 where text_general_code in "
             f"('Aggravated Assault Firearm','Aggravated Assault No Firearm') and dispatch_date between '{start}' and '{end}' group by 1 order by 1")
    if not f.exists():
        r = _get("https://phl.carto.com/api/v2/sql", {"q": q})
        f.write_text(json.dumps({"query": q, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rows": r.json()["rows"]}))
    d = json.loads(f.read_text())
    SRC.setdefault("philadelphia", []).append({"kind": "carto-sql", "url": "https://phl.carto.com/api/v2/sql", "publisher": "City of Philadelphia (OpenDataPhilly)",
                                               "query": d["query"], "fetched": d["fetched"], "n_rows": len(d["rows"])})
    return _series(d["rows"])


def phoenix(start, end):
    f = RAW / "phoenix" / "crimestat.csv"
    url = ("https://www.phoenixopendata.com/dataset/cc08aace-9ca9-467f-b6c1-f0879ab1a358/resource/"
           "0ce3411a-2fc6-4302-a33f-167f68608a20/download/crime-data_crime-data_crimestat.csv")
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, headers=UA, timeout=900)
        r.raise_for_status()
        f.write_bytes(r.content)
    df = pd.read_csv(f, usecols=["INC NUMBER", "OCCURRED ON", "UCR CRIME CATEGORY"], dtype=str)
    df = df[df["UCR CRIME CATEGORY"] == "AGGRAVATED ASSAULT"]
    d = pd.to_datetime(df["OCCURRED ON"].str.split().str[0], format="%m/%d/%Y", errors="coerce")
    s = df.assign(d=d).dropna(subset=["d"]).groupby("d")["INC NUMBER"].nunique()
    SRC.setdefault("phoenix", []).append({"kind": "ckan-csv", "url": url, "publisher": "City of Phoenix Open Data, Police Department crime data",
                                          "file_bytes": f.stat().st_size, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(f.stat().st_mtime)),
                                          "filter": "UCR CRIME CATEGORY = AGGRAVATED ASSAULT; distinct INC NUMBER by date of OCCURRED ON"})
    return s.loc[start:end]


def tucson(start, end):
    f = RAW / "tucson" / "aggassault.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    base = "https://services3.arcgis.com/9coHY2fvuFjG9HQX/arcgis/rest/services/TPDOpenData_ReportedCrimes_{y}/FeatureServer/0/query"
    if not f.exists():
        rows = []
        for y in range(2018, 2027):
            off = 0
            while True:
                r = _get(base.format(y=y), {"where": "UCRSummaryDescription='ASSAULT, AGGRAVATED'", "outFields": "IncidentNumber,OccurredDate", "returnGeometry": "false",
                                            "orderByFields": "OBJECTID", "resultOffset": off, "resultRecordCount": 1000, "f": "json"})
                fs = r.json().get("features", [])
                rows += [[y, x["attributes"]["IncidentNumber"], x["attributes"]["OccurredDate"]] for x in fs]
                if len(fs) < 1000:
                    break
                off += 1000
        f.write_text(json.dumps({"fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rows": rows}))
    d = json.loads(f.read_text())
    df = pd.DataFrame(d["rows"], columns=["layer", "inc", "date"])
    df["d"] = pd.to_datetime(df["date"].astype(str).str[:10], errors="coerce")
    s = df.dropna(subset=["d"]).groupby("d")["inc"].nunique()
    SRC.setdefault("tucson", []).append({"kind": "arcgis-featureserver", "url": base.replace("{y}", "<year>"), "publisher": "Tucson Police Department open data (gisdata.tucsonaz.gov)",
                                         "filter": "UCRSummaryDescription = 'ASSAULT, AGGRAVATED'; distinct IncidentNumber by OccurredDate; layers 2018 to 2026",
                                         "fetched": d["fetched"], "n_rows": len(df)})
    return s.loc[start:end]


def counts(city, start, end):
    if city == "phoenix":
        return phoenix(start, end), None
    if city == "tucson":
        return tucson(start, end), None
    if city == "dallas":
        # date1 (date of occurrence) is stored as text, so rows are fetched and counted here
        rows, src = _soc("https://www.dallasopendata.com", "qv6i-rri7", select="incidentnum, date1", where="nibrs_crime like 'AGG ASSAULT%'", order="incidentnum, date1")
        SRC.setdefault(city, []).append(src)
        df = pd.DataFrame(rows).dropna(subset=["date1"])
        df["d"] = pd.to_datetime(df["date1"].str[:10], errors="coerce")
        return df.dropna(subset=["d"]).groupby("d")["incidentnum"].nunique().loc[start:end], None
    if city == "austin":
        return soc_daily(city, "https://data.austintexas.gov", "fdj4-gpfu", "occ_date", "category_description='Aggravated Assault'", start, end), None
    if city == "los_angeles":
        return los_angeles(start, end), None
    if city == "philadelphia":
        return philadelphia(start, end), philadelphia("2015-01-01", end, shootings=True)
    if city == "chicago":
        a = soc_daily(city, "https://data.cityofchicago.org", "ijzp-q8t2", "date", "fbi_code in ('04A','04B')", start, end)
        s = soc_daily(city, "https://data.cityofchicago.org", "gumc-mgzr", "date", "gunshot_injury_i in ('Y','YES')", "2010-01-01", end, "count(distinct case_number)")
        return a, s
    if city == "new_york":
        a = soc_daily(city, "https://data.cityofnewyork.us", "qgea-i56i", "cmplnt_fr_dt", "ky_cd=106", start, end)
        s = soc_daily(city, "https://data.cityofnewyork.us", "5ucz-vwe8", "occur_date", "1=1", start, END, "count(distinct incident_key)")
        return a, s
    raise KeyError(city)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for city, (label, station, start, end) in CITIES.items():
        a, s = counts(city, start, end)
        w, srcw = noaa.daily(station)
        SRC[city].append(srcw)
        idx = pd.date_range(start, END if s is not None else end, freq="D")
        df = pd.DataFrame(index=idx)
        df["n"] = a.reindex(idx).fillna(0).astype(int)
        df.loc[df.index > end, "n"] = pd.NA
        if s is not None:
            df["shoot"] = s.reindex(idx).fillna(0).astype(int)
            df.loc[df.index < s.index.min(), "shoot"] = pd.NA
        df = df.join(w[["TMAX", "TMIN", "PRCP"]])
        df["dow"], df["month"], df["year"], df["dom1"] = df.index.day_of_week, df.index.month, df.index.year, (df.index.day == 1).astype(int)
        df["hol"] = df.index.isin(holidays(start, END)).astype(int)
        df["wet"] = (df["PRCP"] >= 1.0).astype(int)
        df.index.name = "date"
        df.to_csv(OUT / f"daily_{city}.csv")
        summary[city] = {"label": label, "station": station, "start": start, "end": end, "days": int(df["n"].notna().sum()),
                         "tmax_missing": int(df["TMAX"].isna().sum()), "total": int(df["n"].sum()),
                         "by_year": {int(k): int(v) for k, v in df.groupby("year")["n"].sum().items()}}
        print(city, {k: v for k, v in summary[city].items() if k != "by_year"})
        print("   by year:", summary[city]["by_year"])
    (OUT / "sources.json").write_text(json.dumps({"summary": summary, "sources": SRC}, indent=1, default=str))


if __name__ == "__main__":
    main()
