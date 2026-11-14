"""Round 6 answer, exploratory check: the heat-extremes estimates on a day from 06:00 to 05:59.

The referee of heat-extremes-downturn found that incidents from 00:01 to 05:59 are counted on
a calendar date whose maximum comes ten or more hours later. This script rebuilds each city's
daily file with those incidents counted on the previous date, wherever the published data carry
a time of day, and then runs the registered test.py and describe.py unchanged on the rebuilt
files. It decides no verdict (PRECEDENCE rule 4): the registered measure is the calendar date.

Time of day by city:
  Phoenix       time of occurrence in the city file, to 2 September 2025; the series ends on
                31 August 2025 here, because the file carries no time after that
  Tucson        no time of day is published; the calendar-date series is used unchanged
  Dallas        time1 (referee's incident file in ~/opt/nyc-concordance/heat_extremes/referee/)
  Austin        occ_time (referee's incident file)
  Los Angeles   time_occ
  Chicago       the time in `date` (aggravated assaults and shooting victims)
  New York      cmplnt_fr_tm (felony assaults); occur_time (shootings, cached query of heat_solutions)
  Philadelphia  dispatch_time (aggravated assaults, the time that belongs to the published date);
                `time` (shootings)
Incidents at exactly 00:00 are left on their date in the assault series, as in the referee's
check, because several portals use 00:00 when the time is unknown. The last day of a series
has no following morning in the data where the series ends with the file, and is dropped.

Run from the repository root (after the referee's incident files exist):
    ~/.venvs/nyc-concordance/bin/python analyses/critique/round6_six_am_extremes.py
Writes data/derived/round6_heat/extremes_six_am/ (daily_<city>.csv, test_results.json, curves.csv,
curves_pct.csv, describe.json) and data/derived/round6_heat/six_am_extremes.json.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import referee_heat_extremes as RX  # noqa: E402  (data loaders only)
from analyses.heat_extremes import build as B  # noqa: E402
from analyses.heat_extremes import describe as D  # noqa: E402
from analyses.heat_extremes import model as m  # noqa: E402
from analyses.heat_extremes import test as T  # noqa: E402
from analyses.heat_solutions import run as HS  # noqa: E402

warnings.filterwarnings("ignore")
REG = ROOT / "data/derived/heat_extremes"
OUT = ROOT / "data/derived/round6_heat"
SIX = OUT / "extremes_six_am"
SIX.mkdir(parents=True, exist_ok=True)
RAW = Path.home() / "opt/nyc-concordance/heat_extremes/round6"
RAW.mkdir(parents=True, exist_ok=True)
SRC = []


def early_from_incidents(x, hh, mm):
    """Distinct incidents from 00:01 to 05:59 by calendar date."""
    night = (hh < 6) & ~((hh == 0) & (mm == 0))
    return x[night].groupby("d")["inc"].nunique(), float(night.mean())


def soc_early(domain, dataset, datefield, where, count="count(*)"):
    rows, src = B._soc(domain, dataset, select=f"date_trunc_ymd({datefield}) as d, {count} as n", where=where, group="d", order="d")
    SRC.append(src)
    return B._series(rows)


def carto_early(name, q):
    f = RAW / f"philadelphia_{name}_early.json"
    if not f.exists():
        r = B._get("https://phl.carto.com/api/v2/sql", {"q": q})
        f.write_text(json.dumps({"query": q, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rows": r.json()["rows"]}))
    d = json.loads(f.read_text())
    SRC.append({"kind": "carto-sql", "url": "https://phl.carto.com/api/v2/sql", "query": d["query"], "fetched": d["fetched"], "n_rows": len(d["rows"])})
    return B._series(d["rows"])


def early_counts():
    """{city: {column: (series of early counts by calendar date, last date with a following morning in the data or None)}}"""
    E, share = {}, {}
    x = RX.phoenix_incidents()
    e, share["phoenix"] = early_from_incidents(x, pd.to_numeric(x["t"].str[:2], errors="coerce"), pd.to_numeric(x["t"].str[3:5], errors="coerce"))
    E["phoenix"] = {"n": (e, "2025-08-31")}
    x = RX.dallas_incidents()
    e, share["dallas"] = early_from_incidents(x, pd.to_numeric(x["t"].str[:2], errors="coerce"), pd.to_numeric(x["t"].str[3:5], errors="coerce"))
    E["dallas"] = {"n": (e, None)}
    x = RX.austin_incidents()
    # the registered Austin series counts rows; the referee's file has one row per incident report
    hh, mm = pd.to_numeric(x["t"].str[:2], errors="coerce"), pd.to_numeric(x["t"].str[3:5], errors="coerce")
    night = (hh < 6) & ~((hh == 0) & (mm == 0))
    E["austin"] = {"n": (x[night].groupby("d").size(), None)}
    share["austin"] = float(night.mean())
    la = "crm_cd in ('230','231','235','236') and time_occ between '0001' and '0559'"
    a = soc_early("https://data.lacity.org", "63jg-8b9z", "date_occ", "date_occ between '2010-01-01T00:00:00' and '2019-12-31T23:59:59' AND " + la)
    b = soc_early("https://data.lacity.org", "2nrs-mtv8", "date_occ", "date_occ between '2020-01-01T00:00:00' and '2024-01-01T23:59:59' AND " + la)
    E["los_angeles"] = {"n": (a.add(b, fill_value=0), None)}
    hm = "date_extract_hh(date) < 6 and not (date_extract_hh(date) = 0 and date_extract_mm(date) = 0)"
    E["chicago"] = {
        "n": (soc_early("https://data.cityofchicago.org", "ijzp-q8t2", "date", f"date between '2006-01-01T00:00:00' and '2026-09-01T23:59:59' AND fbi_code in ('04A','04B') AND {hm}"), None),
        "shoot": (soc_early("https://data.cityofchicago.org", "gumc-mgzr", "date", "date between '2010-01-01T00:00:00' and '2026-09-01T23:59:59' AND gunshot_injury_i in ('Y','YES') AND date_extract_hh(date) < 6",
                            "count(distinct case_number)"), None)}
    inc, _, _, _ = HS.fetch()
    inc["d"] = pd.to_datetime(inc["d"]).dt.normalize()
    inc["hour"] = inc["t"].str.split(":").str[0].astype(int)
    E["new_york"] = {
        "n": (soc_early("https://data.cityofnewyork.us", "qgea-i56i", "cmplnt_fr_dt",
                        "cmplnt_fr_dt between '2006-01-01T00:00:00' and '2026-01-01T23:59:59' AND ky_cd=106 AND cmplnt_fr_tm between '00:00:01' and '05:59:59'"), None),
        "shoot": (inc[inc.hour < 6].groupby("d").size(), "2026-08-30")}
    E["philadelphia"] = {
        "n": (carto_early("aggassault", "select dispatch_date as d, count(*) as n from incidents_part1_part2 where text_general_code in "
                          "('Aggravated Assault Firearm','Aggravated Assault No Firearm') and dispatch_date between '2006-01-01' and '2026-09-01' "
                          "and dispatch_time < '06:00:00' group by 1 order by 1"), None),
        "shoot": (carto_early("shootings", "select date_::date as d, count(*) as n from shootings where date_ between '2015-01-01' and '2026-09-01' "
                              "and time < '06:00:00' group by 1 order by 1"), None)}
    return E, share


def rebuild(E):
    info = {}
    for c in m.CITIES:
        d = pd.read_csv(REG / f"daily_{c}.csv", parse_dates=["date"]).set_index("date")
        info[c] = {}
        for col, (e, last) in E.get(c, {}).items():
            have = d[col].notna()
            e = e.reindex(pd.date_range(d.index.min(), d.index.max() + pd.Timedelta(days=1), freq="D")).fillna(0)
            new = d[col] - e.reindex(d.index).values + e.shift(-1).reindex(d.index).values
            end = pd.Timestamp(last) if last else d.index[have].max() - pd.Timedelta(days=1)
            new[(d.index > end) | ~have] = np.nan
            assert (new.dropna() >= 0).all(), (c, col, new.min())
            info[c][col] = {"calendar_total": float(d.loc[have & (d.index <= end), col].sum()), "six_am_total": float(new.sum()),
                            "early_share": float(e.reindex(d.index)[have & (d.index <= end)].sum() / d.loc[have & (d.index <= end), col].sum()), "ends": str(end.date())}
            d[col] = new
        d.to_csv(SIX / f"daily_{c}.csv")
    return info


def wave(city, y):
    """Days two and later of a run of days at 32 C or more against first and isolated hot days (the model of describe.ny_heatwaves)."""
    d = m.load(city, y)
    full = d["TMAX"].reindex(pd.date_range(d.index.min(), d.index.max(), freq="D"))
    hot = (full >= 32.0).astype(int)
    run = (hot != hot.shift()).cumsum()
    pos = hot.groupby(run).cumsum()
    d["hotday"] = hot.reindex(d.index)
    d["later"] = ((hot == 1) & (pos >= 2)).astype(int).reindex(d.index)
    for k in (15, 21, 27):
        d[f"s{k}"] = np.clip(d["TMAX"] - k, 0, None)
    a = m.nb_alpha(d, y)
    r = smf.glm(f"{y} ~ hotday + later + TMAX + s15 + s21 + s27 + {m.CONTROLS}", d, family=sm.families.NegativeBinomial(alpha=a)).fit(cov_type="HC0")
    return {"log": float(r.params["later"]), "se": float(r.bse["later"]), **{k: v for k, v in m.rr({"log": float(r.params["later"]), "se": float(r.bse["later"])}).items() if k in ("estimate", "lo", "hi")}}


def waves():
    w = {f"{c}_{y}": wave(c, y) for c, y in (("new_york", "shoot"), ("new_york", "n"), ("chicago", "shoot"), ("philadelphia", "shoot"), ("chicago", "n"), ("philadelphia", "n"))}
    p = m.pool([w["chicago_shoot"], w["philadelphia_shoot"]])["random"]
    w["chicago_and_philadelphia_shootings_pooled"] = {k: p[k] for k in ("estimate", "lo", "hi")}
    return w


def summary(der):
    """The estimates that docs/heat_extremes.md quotes, from the files in `der`."""
    t = json.loads((der / "test_results.json").read_text())
    ds = json.loads((der / "describe.json").read_text())
    cv = pd.read_csv(der / "curves.csv")
    cp = pd.read_csv(der / "curves_pct.csv")
    f = lambda e: {k: e[k] for k in ("estimate", "lo", "hi")}
    S = {"pooled": f(t["pooled"]["random"]), "verdict_by_registered_rule": t["verdict"], "I2": t["pooled"]["I2"],
         "cities": {c: {**f(t["cities"][c]), "days": t["cities"][c]["days"], "days_ref": t["cities"][c]["days_ref"]} for c in T.QUALIFYING}}
    for k in ("S1_year_month_strata", "S2_may_sep_only", "S3_without_2020_2021", "S4_35_38_vs_32_35", "S5_38_41_vs_32_35", "S6_41_plus_vs_32_35"):
        S[k] = f(t["sensitivity"][k]["pooled"]["random"])
    lin = t["linear_alternative"]["pooled"]["random"]
    S["linear_prediction"] = f(lin)
    S["z_observed_below_linear"] = float((lin["log"] - t["pooled"]["random"]["log"]) / np.hypot(lin["se"], t["pooled"]["random"]["se"]))
    S["curve_hot4_vs_20_23"] = {r.bin: {"estimate": r.estimate, "lo": r.lo, "hi": r.hi} for r in cv[cv.city == "pooled_hot4"].itertuples()
                                if r.bin in ("[29.0, 32.0)", "[32.0, 35.0)", "[35.0, 38.0)", "[38.0, 41.0)", "[41.0, 44.0)")}
    g = cv[(cv.city == "phoenix") & (cv.bin == "[44.0, inf)")]
    S["phoenix_44_plus"] = {k: float(g[k].iloc[0]) for k in ("estimate", "lo", "hi")}
    S["last_bin_35_38"] = {c: {k: float(cv[(cv.city == c) & (cv.bin == "[35.0, 38.0)")][k].iloc[0]) for k in ("estimate", "lo", "hi")}
                           for c in ("los_angeles", "chicago", "new_york", "philadelphia")}
    S["slope_20_to_35_per_5C"] = f(ds["slopes"]["pooled_20_to_35"]["random"])
    S["slope_above_35_per_5C"] = f(ds["slopes"]["pooled_above_35"]["random"])
    S["dallas_slope_above_35_per_5C"] = f(ds["slopes"]["dallas"]["per5C_above_35"])
    st = ds["stacked"]
    S["aic_degrees"], S["aic_percentile"] = st["common_degrees"]["aic"], st["common_percentile"]["aic"]
    S["aic_degrees_better_by"] = st["common_percentile"]["aic"] - st["common_degrees"]["aic"]
    S["city_days_stacked"] = st["n_days"]
    S["top_percentile_bin_vs_50_70"] = {c: float(cp[(cp.city == c) & (cp.bin == "[98.0, 100.0001)")]["estimate"].iloc[0]) for c in m.CITIES
                                        if len(cp[(cp.city == c) & (cp.bin == "[98.0, 100.0001)")])}
    h = ds["ny_heatwaves"]
    S["ny_heatwave_shootings"] = {k: f(h["shootings"][k]) for k in ("day1", "day2", "day3", "day4plus", "later_vs_first_or_isolated")}
    S["ny_heatwave_felony_assaults_later"] = f(h["felony_assaults"]["later_vs_first_or_isolated"])
    return S


def main():
    E, share = early_counts()
    info = rebuild(E)
    res = {"note": "Exploratory, run after the outcome; decides no verdict (rule 4). calendar = the registered files; six_am = incidents "
                   "from 00:01 to 05:59 counted on the previous date (Tucson unchanged: no time of day is published).",
           "share_00_01_to_05_59_of_incident_file": share, "series": info}
    m.DER = REG
    res["calendar"] = summary(REG)
    res["calendar"]["heat_waves"] = waves()
    m.DER = SIX
    T.main()
    D.main()
    res["six_am"] = summary(SIX)
    res["six_am"]["heat_waves"] = waves()
    m.DER = REG
    res["sources"] = SRC
    (OUT / "six_am_extremes.json").write_text(json.dumps(res, indent=1, default=str))
    print("\n\n==== side by side ====")
    print(json.dumps({k: res[k] for k in ("share_00_01_to_05_59_of_incident_file", "series")}, indent=1))

    def show(k, a, b):
        if isinstance(a, dict) and "estimate" in a:
            print(f"  {k:58s} {a['estimate']:.3f} ({a['lo']:.3f} to {a['hi']:.3f})   |   {b['estimate']:.3f} ({b['lo']:.3f} to {b['hi']:.3f})")
        elif isinstance(a, dict):
            for kk in a:
                show(f"{k}.{kk}", a[kk], b[kk])
        else:
            print(f"  {k:58s} {a}   |   {b}")
    for k in res["calendar"]:
        show(k, res["calendar"][k], res["six_am"][k])


if __name__ == "__main__":
    main()
