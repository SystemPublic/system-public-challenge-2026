"""Referee re-estimation for heat-extremes-downturn. Written by the blind referee, not the registrant.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_heat_extremes.py

It rebuilds the daily series of the four deciding cities with its own code from the raw files
(Phoenix CSV, Tucson JSON, the cached Dallas query, GHCN-Daily files in data/cache/noaa), refits
the deciding model without importing analyses/heat_extremes, and runs variants the registrant
did not run. Incident-level files for Dallas and Austin (time of day, report date, family
violence flag) and five second weather stations were fetched by the referee on 13 Nov 2026 into
~/opt/nyc-concordance/heat_extremes/referee/ ; sections that need them are skipped when the
folder is absent. It prints its results and writes no file.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pandas.tseries.holiday import USFederalHolidayCalendar
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data/derived/heat_extremes"
NOAA = ROOT / "data/cache/noaa"
SOC = ROOT / "data/cache/socrata"
RAW = Path.home() / "opt/nyc-concordance/heat_extremes"
REF = RAW / "referee"
CAL = "C(dow) + C(month) + C(year) + hol + dom1 + wet"
CALYM = "C(dow) + C(ym) + hol + dom1 + wet"
HOT4 = ["phoenix", "tucson", "dallas", "austin"]
SPAN = {"phoenix": ("2015-11-01", "2025-11-30", "USW00023183"), "tucson": ("2018-01-01", "2026-08-31", "USW00023160"),
        "dallas": ("2017-01-01", "2026-08-31", "USW00013960"), "austin": ("2003-01-01", "2026-08-31", "USW00013958")}
ALT = {"phoenix": {"Deer Valley": "USW00003184"}, "dallas": {"DFW": "USW00003927"}, "austin": {"Bergstrom": "USW00013904"}}
EDGES = [-np.inf, 8, 14, 20, 23, 26, 29, 32, 35, 38, np.inf]
LAB = ["b00", "b08", "b14", "b20", "b23", "b26", "b29", "ref", "b35", "hot"]


# ---------- data ----------
def weather(sid, folder=NOAA):
    w = pd.read_csv(folder / f"{sid}.csv", low_memory=False, usecols=["DATE", "TMAX", "TMIN", "PRCP"])
    w["DATE"] = pd.to_datetime(w["DATE"])
    w = w.set_index("DATE").asfreq("D")
    return w[["TMAX", "TMIN", "PRCP"]] / 10.0


def phoenix_incidents():
    df = pd.read_csv(RAW / "phoenix/crimestat.csv", dtype=str, usecols=["INC NUMBER", "OCCURRED ON", "UCR CRIME CATEGORY", "PREMISE TYPE"])
    df = df[df["UCR CRIME CATEGORY"] == "AGGRAVATED ASSAULT"].dropna(subset=["OCCURRED ON"])
    parts = df["OCCURRED ON"].str.split()
    df["d"] = pd.to_datetime(parts.str[0], format="%m/%d/%Y", errors="coerce")
    df["t"] = parts.str[1]
    df = df.dropna(subset=["d"]).drop_duplicates("INC NUMBER")
    return df.rename(columns={"INC NUMBER": "inc", "PREMISE TYPE": "premise"})


def tucson_incidents():
    d = json.loads((RAW / "tucson/aggassault.json").read_text())
    df = pd.DataFrame(d["rows"], columns=["layer", "inc", "date"])
    df["d"] = pd.to_datetime(df["date"].astype(str).str[:10], errors="coerce")
    return df.dropna(subset=["d"]).drop_duplicates("inc")


def dallas_incidents():
    f = REF / "dallas_incidents.json"
    if f.exists():
        df = pd.DataFrame(json.loads(f.read_text())["rows"])
    else:
        df = pd.DataFrame(json.loads((SOC / "qv6i-rri7-da200c3f49f63cee3806147b.json").read_text())["rows"])
    df["d"] = pd.to_datetime(df["date1"].str[:10], errors="coerce")
    df = df.dropna(subset=["d"]).rename(columns={"incidentnum": "inc"})
    if "time1" in df:
        df["t"] = df["time1"]
        df["rep"] = pd.to_datetime(df["reporteddate"].str[:10], errors="coerce")
    return df.sort_values(["inc", "d"]).drop_duplicates(["inc", "d"])


def austin_incidents():
    f = REF / "austin_incidents.json"
    if not f.exists():
        return None
    df = pd.DataFrame(json.loads(f.read_text())["rows"])
    df["d"] = pd.to_datetime(df["occ_date"].str[:10], errors="coerce")
    df["rep"] = pd.to_datetime(df["rep_date"].str[:10], errors="coerce")
    tt = df["occ_time"].astype(str).str.replace(":", "").str.zfill(4)
    df["t"] = tt.str[:2] + ":" + tt.str[2:4]
    df["fv"] = (df["family_violence"] == "Y") | df["crime_type"].str.contains("FAM|STRANG", na=False)
    return df.dropna(subset=["d"]).rename(columns={"incident_report_number": "inc"})


def frame(city, counts, w=None, start=None, end=None):
    """Daily frame from a series of counts indexed by date."""
    s, e, sid = SPAN[city]
    s, e = start or s, end or e
    w = weather(sid) if w is None else w
    idx = pd.date_range(s, e, freq="D")
    d = pd.DataFrame({"n": counts.reindex(idx).fillna(0).astype(int)}, index=idx).join(w)
    d = d.dropna(subset=["TMAX"])
    d["dow"], d["month"], d["year"] = d.index.dayofweek, d.index.month, d.index.year
    d["ym"] = d["year"] * 100 + d["month"]
    d["dom1"] = (d.index.day == 1).astype(int)
    hol = USFederalHolidayCalendar().holidays(start=idx.min(), end=idx.max())
    d["hol"] = d.index.isin(hol).astype(int)
    d["wet"] = (d["PRCP"].fillna(0) >= 1.0).astype(int)
    d["tb"] = pd.cut(d["TMAX"], EDGES, right=False, labels=LAB).astype(str)
    return d


def derived(city, y="n"):
    d = pd.read_csv(DER / f"daily_{city}.csv", parse_dates=["date"]).set_index("date").dropna(subset=[y, "TMAX"])
    d[y] = d[y].astype(int)
    d["wet"] = d["wet"].fillna(0)
    d["ym"] = d["year"] * 100 + d["month"]
    d["tb"] = pd.cut(d["TMAX"], EDGES, right=False, labels=LAB).astype(str)
    return d


# ---------- models ----------
def alpha_ml(d, y="n", cal=CAL):
    try:
        a = float(smf.negativebinomial(f"{y} ~ I(TMAX/5) + {cal}", d).fit(disp=0, maxiter=300).params["alpha"])
        return max(a, 1e-4) if np.isfinite(a) else 0.05
    except Exception:
        return 0.05


TERM = "C(tb, Treatment(reference='ref'))"
KEY = TERM + "[T.hot]"


def fit(d, y="n", cal=CAL, fam="nb", alpha=None, cov="HC0", key=KEY, term=TERM):
    if fam == "nb":
        alpha = alpha_ml(d, y) if alpha is None else alpha
        family = sm.families.NegativeBinomial(alpha=alpha)
    else:
        family = sm.families.Poisson()
    kw = {"cov_type": "HAC", "cov_kwds": {"maxlags": 7}} if cov == "HAC" else {"cov_type": cov}
    if cov == "scale":
        r = smf.glm(f"{y} ~ {term} + {cal}", d, family=family).fit(scale="X2")
    else:
        r = smf.glm(f"{y} ~ {term} + {cal}", d, family=family).fit(**kw)
    return {"log": float(r.params[key]), "se": float(r.bse[key]), "alpha": alpha}


def pool(es, hk=False):
    b = np.array([e["log"] for e in es]); v = np.array([e["se"] for e in es]) ** 2
    w = 1 / v; k = len(b)
    fe = (w * b).sum() / w.sum()
    Q = float((w * (b - fe) ** 2).sum())
    c = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - (k - 1)) / c)
    wr = 1 / (v + tau2)
    m = float((wr * b).sum() / wr.sum()); se = float(np.sqrt(1 / wr.sum())); crit = 1.96
    if hk:  # Hartung-Knapp-Sidik-Jonkman standard error with a t quantile on k-1 degrees of freedom
        se = float(np.sqrt((wr * (b - m) ** 2).sum() / ((k - 1) * wr.sum())))
        crit = float(stats.t.ppf(0.975, k - 1))
    return {"est": float(np.exp(m)), "lo": float(np.exp(m - crit * se)), "hi": float(np.exp(m + crit * se)), "log": m, "se": se, "Q": Q, "tau2": tau2}


def s(e):
    if "est" in e:
        return f"{e['est']:.3f} ({e['lo']:.3f} to {e['hi']:.3f})"
    return f"{np.exp(e['log']):.3f} ({np.exp(e['log'] - 1.96 * e['se']):.3f} to {np.exp(e['log'] + 1.96 * e['se']):.3f})"


def row(name, es, cities=HOT4):
    es = {c: e for c, e in es.items() if e is not None}
    p = pool(list(es.values())) if len(es) > 1 else None
    print(f"{name:<44}" + "  ".join(f"{c[:3]} {s(es[c]) if c in es else '-':<24}" for c in cities) + ("  pooled " + s(p) if p else ""))
    return p


def main():
    pd.set_option("display.width", 220)
    print("== A. Rebuilt daily counts against the registrant's derived files ==")
    inc = {"phoenix": phoenix_incidents(), "tucson": tucson_incidents(), "dallas": dallas_incidents(), "austin": austin_incidents()}
    F, FD = {}, {}
    for c in HOT4:
        FD[c] = derived(c)
        if inc[c] is None:
            F[c] = FD[c]
            continue
        cnt = inc[c].groupby("d")["inc"].nunique()
        F[c] = frame(c, cnt)
        j = F[c][["n", "TMAX"]].join(FD[c][["n", "TMAX", "hol"]], rsuffix="_reg", how="outer")
        print(c, "days", len(F[c]), "reg days", len(FD[c]), "days where counts differ", int((j.n != j.n_reg).sum()), "max TMAX diff", float((j.TMAX - j.TMAX_reg).abs().max()),
              "holiday flag differs on", int((F[c]["hol"] != FD[c]["hol"].reindex(F[c].index)).sum()), "total", int(F[c].n.sum()), int(FD[c].n.sum()))
    for c in HOT4:  # use the registrant's holiday flag so that only counts and temperatures are the referee's own
        F[c]["hol"] = FD[c]["hol"].reindex(F[c].index).fillna(F[c]["hol"]).astype(int)

    print("\n== B. Deciding contrast, 38 C and above against 32 to 35 C ==")
    A = {c: alpha_ml(F[c]) for c in HOT4}
    base = {c: fit(F[c], alpha=A[c]) for c in HOT4}
    p = row("registered model, referee code", base)
    print("   Q", round(p["Q"], 2), "tau2", p["tau2"], "z against 1.00", round(p["log"] / p["se"], 2), "p", round(2 * stats.norm.sf(abs(p["log"] / p["se"])), 4))
    print("   Hartung-Knapp interval (t on 3 df):", s(pool(list(base.values()), hk=True)))
    print("   z against the registered downturn 0.98:", round((p["log"] - np.log(0.98)) / p["se"], 2), " against the linear band lower end 1.06:", round((p["log"] - np.log(1.06)) / p["se"], 2))
    pv = [2 * stats.norm.sf(abs(e["log"] / e["se"])) for e in base.values()]
    print("   city p-values against 1.00:", [round(x, 3) for x in pv])

    print("\n== C. Variants (pooled DerSimonian-Laird unless stated) ==")
    row("Poisson, HC0", {c: fit(F[c], fam="pois") for c in HOT4})
    row("Poisson, Pearson-scaled errors", {c: fit(F[c], fam="pois", cov="scale") for c in HOT4})
    row("NB, HAC errors 7 lags", {c: fit(F[c], alpha=A[c], cov="HAC") for c in HOT4})
    row("year-by-month terms (S1)", {c: fit(F[c], cal=CALYM, alpha=A[c]) for c in HOT4})
    row("year-by-month and month-by-weekday terms", {c: fit(F[c], cal=CALYM + " + C(month):C(dow)", alpha=A[c]) for c in HOT4})
    row("May to September (S2)", {c: fit(F[c][F[c].month.between(5, 9)], alpha=A[c]) for c in HOT4})
    row("June to September, year-by-month", {c: fit(F[c][F[c].month.between(6, 9)], cal=CALYM, alpha=A[c]) for c in HOT4})
    row("without 2020 and 2021 (S3)", {c: fit(F[c][~F[c].year.isin([2020, 2021])], alpha=A[c]) for c in HOT4})
    row("without 2020 only", {c: fit(F[c][F[c].year != 2020], alpha=A[c]) for c in HOT4})
    row("2017 to 2025 in every city", {c: fit(F[c][F[c].year.between(2018 if c == "tucson" else 2017, 2025)], alpha=A[c]) for c in HOT4})
    row("TMIN added (linear)", {c: fit(F[c].dropna(subset=["TMIN"]), cal=CAL + " + TMIN", alpha=A[c]) for c in HOT4})
    row("rain amount and yesterday's TMAX added", {c: fit(F[c].assign(pr=F[c].PRCP.fillna(0), l1=F[c].TMAX.shift(1)).dropna(subset=["l1"]), cal=CAL + " + pr + l1", alpha=A[c]) for c in HOT4})
    for m in (3, 6, 12):
        row(f"last {m} months of each series dropped", {c: fit(F[c][F[c].index <= F[c].index.max() - pd.DateOffset(months=m)], alpha=A[c]) for c in HOT4})
    ph_cut = {**F, "phoenix": F["phoenix"][:"2025-08-31"]}
    row("Phoenix ends 31 Aug 2025 (records system change)", {c: fit(ph_cut[c], alpha=A[c]) for c in HOT4})
    ph_cut2 = {**F, "phoenix": F["phoenix"]["2017-01-01":"2025-08-31"]}
    row("Phoenix 2017 to Aug 2025", {c: fit(ph_cut2[c], alpha=A[c]) for c in HOT4})
    # wider reference bin and hot bin from 100 F
    for name, edges in (("reference 29 to 35 C", [-np.inf, 8, 14, 20, 23, 26, 29, 35, 38, np.inf]), ("hot bin from 37.7 C (100 F)", [-np.inf, 8, 14, 20, 23, 26, 29, 32, 35, 37.7, np.inf])):
        labs = ["b00", "b08", "b14", "b20", "b23", "b26", "ref", "b35", "hot"] if len(edges) == 10 else LAB
        row(name, {c: fit(F[c].assign(tb=pd.cut(F[c].TMAX, edges, right=False, labels=labs).astype(str)), alpha=A[c]) for c in HOT4})
    print("leave one city out:", {c: s(pool([base[x] for x in HOT4 if x != c])) for c in HOT4})

    print("\n== D. Where the days at 38 C and above fall ==")
    for c in HOT4:
        d = F[c]
        hot, ref = d.tb == "hot", d.tb == "ref"
        by_m = pd.crosstab(d.month, d.tb)[["ref", "b35", "hot"]]
        ymh, ymr = d[hot].groupby("ym").size(), d[ref].groupby("ym").size()
        both = ymh.index.intersection(ymr.index)
        print(c, "hot days by month", by_m["hot"][by_m["hot"] > 0].to_dict(), "| reference days by month", by_m["ref"][by_m["ref"] > 0].to_dict())
        print("   hot days by year", d[hot].groupby("year").size().to_dict())
        print(f"   share of hot days in a year-month that also has a reference day: {ymh.reindex(both).sum() / hot.sum():.2f}; share of reference days in a year-month with a hot day: {ymr.reindex(both).sum() / ref.sum():.2f}")
    loo = []
    yrs = sorted(set().union(*[set(F[c].year) for c in HOT4]))
    for y in yrs:
        es = [fit(F[c][F[c].year != y], alpha=A[c]) for c in HOT4]
        pp = pool(es)
        loo.append((y, pp["est"], pp["lo"]))
    print("leave one calendar year out, pooled estimate and lower limit:")
    print("  ", "  ".join(f"{y}:{e:.3f}/{l:.3f}" for y, e, l in loo))
    print("   years whose removal puts the lower limit at or below 1.00:", [y for y, e, l in loo if l <= 1.0])
    # interaction of the hot bin with summer period
    row("hot days in Jun-Aug only vs ref (hot in other months separate)", {c: fit(F[c].assign(tb=np.where((F[c].tb == "hot") & ~F[c].month.between(6, 8), "hot_shoulder", F[c].tb)), alpha=A[c]) for c in HOT4})
    row("hot days outside Jun-Aug vs ref", {c: fit(F[c].assign(tb=np.where((F[c].tb == "hot") & ~F[c].month.between(6, 8), "hot_shoulder", F[c].tb)), alpha=A[c], key=TERM + "[T.hot_shoulder]") for c in ["phoenix", "tucson"]}, cities=["phoenix", "tucson"])

    print("\n== E. Recent months and reporting lag ==")
    for c in HOT4:
        d = F[c]
        m = d.n.resample("MS").sum()
        same = m.groupby(m.index.month).transform(lambda x: x.shift(1))
        print(c, "last 12 months, count and ratio to the same month a year earlier:", [(int(a), round(a / b, 2)) for a, b in zip(m.tail(12), same.tail(12))])
    for c in ("dallas", "austin"):
        x = inc[c]
        if x is None or "rep" not in x:
            continue
        lag = (x["rep"] - x["d"]).dt.days.dropna()
        print(c, "report date minus occurrence date, days: share 0:", round(float((lag == 0).mean()), 3), "share 1:", round(float((lag == 1).mean()), 3), "share over 7:", round(float((lag > 7).mean()), 3),
              "share over 30:", round(float((lag > 30).mean()), 3), "share over 365:", round(float((lag > 365).mean()), 4))
        # counts by report date in place of occurrence date
        cr = x.dropna(subset=["rep"]).groupby("rep")["inc"].nunique()
        e = fit(frame(c, cr), alpha=A[c])
        print("   same model with incidents dated by report date:", s(e), " by occurrence date:", s(base[c]))
        same = x[lag.reindex(x.index) <= 1]
        print("   incidents reported within one day of occurrence only:", s(fit(frame(c, same.groupby("d")["inc"].nunique()))))
    t = inc["tucson"]
    print("tucson: share of incidents whose occurrence year differs from the year of the layer that holds them:", round(float((t.d.dt.year != t.layer).mean()), 4))

    print("\n== F. Incidents from 00:00 to 05:59 counted on the previous date ==")
    shifted = {}
    for c in ("phoenix", "dallas", "austin"):
        x = inc[c]
        if x is None or "t" not in x:
            continue
        x = x.copy()
        hh = pd.to_numeric(x["t"].str[:2], errors="coerce")
        mm = pd.to_numeric(x["t"].str[3:5], errors="coerce")
        end = "2025-08-31" if c == "phoenix" else None  # Phoenix publishes no time of day after 2 Sep 2025
        print(c, "share with no time:", round(float(hh.isna().mean()), 3), "share at exactly 00:00:", round(float(((hh == 0) & (mm == 0)).mean()), 3), "share 00:01 to 05:59:", round(float(((hh < 6) & ~((hh == 0) & (mm == 0))).mean()), 3),
              "share 12:00 to 23:59:", round(float((hh >= 12).mean()), 3))
        night = (hh < 6) & ~((hh == 0) & (mm == 0))
        x["sd"] = x["d"] - pd.to_timedelta(night.astype(int), unit="D")
        cal_d = frame(c, x.groupby("d")["inc"].nunique(), end=end)
        sh_d = frame(c, x.groupby("sd")["inc"].nunique(), end=end)
        e0, e1 = fit(cal_d), fit(sh_d)
        day = x[(hh >= 12)]
        e2 = fit(frame(c, day.groupby("d")["inc"].nunique(), end=end))
        e3 = fit(frame(c, x[night].groupby("sd")["inc"].nunique(), end=end))
        e4 = fit(frame(c, x[(hh >= 6) & (hh < 12)].groupby("d")["inc"].nunique(), end=end))
        shifted[c] = e1
        print(f"   calendar date {s(e0)} | 06:00 to 05:59 day {s(e1)} | 12:00 to 23:59 only {s(e2)} | 06:00 to 11:59 only {s(e4)} | 00:01 to 05:59 of the following night {s(e3)}")
    if shifted:
        shifted["tucson"] = base["tucson"]
        row("pooled with the 06:00 day (Tucson calendar, no times)", shifted)

    print("\n== G. Offence definitions ==")
    a = inc["austin"]
    if a is not None:
        print("austin: share flagged family violence or strangulation:", round(float(a.fv.mean()), 3), "| by period:", a.groupby(pd.cut(a.d.dt.year, [2002, 2008, 2014, 2020, 2026]))["fv"].mean().round(3).to_dict())
        print("austin crime types:", a.crime_type.value_counts().head(6).to_dict())
        e_fv = fit(frame("austin", a[a.fv].groupby("d")["inc"].nunique()))
        e_nf = fit(frame("austin", a[~a.fv].groupby("d")["inc"].nunique()))
        print("   austin family violence:", s(e_fv), "| not family violence:", s(e_nf), "| difference z:", round((e_fv["log"] - e_nf["log"]) / np.hypot(e_fv["se"], e_nf["se"]), 2))
        row("pooled with Austin non-family only (as Dallas)", {**base, "austin": e_nf})
    d = inc["dallas"]
    if "nibrs_crime" in d:
        print("dallas nibrs_crime:", d.drop_duplicates("inc").nibrs_crime.value_counts().to_dict())
        res = d.premise.fillna("").str.contains("Residence|Apartment|Home", case=False)
        print("dallas share at a residence:", round(float(res.mean()), 3))
    ph = inc["phoenix"]
    res = ph.premise.fillna("").str.contains("HOUSE|APARTMENT|CONDO|MOBILE HOME|RESIDEN", case=False)
    out = ph.premise.fillna("").str.contains("STREET|PARK|PARKING|BUS STOP|ALLEY|DESERT|OPEN SPACE", case=False)
    print("phoenix share at a residence:", round(float(res.mean()), 3), "share outdoors:", round(float(out.mean()), 3))
    e_r = fit(frame("phoenix", ph[res].groupby("d")["inc"].nunique()))
    e_o = fit(frame("phoenix", ph[out].groupby("d")["inc"].nunique()))
    print("   phoenix residence:", s(e_r), "| outdoors:", s(e_o), "| difference z:", round((e_r["log"] - e_o["log"]) / np.hypot(e_r["se"], e_o["se"]), 2))

    print("\n== H. Second weather station ==")
    alt = {}
    for c, m in ALT.items():
        for name, sid in m.items():
            if not (REF / f"{sid}.csv").exists():
                continue
            w2 = weather(sid, REF)
            cnt = F[c]["n"]
            d2 = frame(c, cnt, w=w2)
            d2["hol"] = FD[c]["hol"].reindex(d2.index).fillna(0).astype(int)
            j = F[c][["TMAX"]].join(w2[["TMAX"]], rsuffix="_alt").dropna()
            hot1, hot2 = j.TMAX >= 38, j.TMAX_alt >= 38
            alt[c] = fit(d2)
            print(f"{c} {name} ({sid}): days {len(d2)}, mean difference alt minus registered {float((j.TMAX_alt - j.TMAX).mean()):+.2f} C, sd {float((j.TMAX_alt - j.TMAX).std()):.2f}, "
                  f"hot days {int(hot1.sum())} registered and {int(hot2.sum())} alt, agreeing {int((hot1 & hot2).sum())}; estimate {s(alt[c])}")
    if alt:
        row("pooled with second stations where available", {**base, **alt})

    print("\n== I. One curve in degrees against one curve in percentiles ==")
    cities = ["phoenix", "tucson", "dallas", "austin", "los_angeles", "philadelphia", "chicago", "new_york"]
    fr = []
    for c in cities:
        d = derived(c)
        d["pct"] = d.TMAX.rank(pct=True) * 100
        d["anom"] = d.TMAX - d.TMAX.mean()
        d["city"] = c
        fr.append(d[["n", "city", "TMAX", "pct", "anom", "dow", "month", "year", "hol", "dom1", "wet"]])
    S = pd.concat(fr)
    cal = "C(city) + C(city):C(dow) + C(city):C(month) + C(city):C(year) + C(city):hol + C(city):dom1 + C(city):wet"
    fam = sm.families.NegativeBinomial(alpha=0.01)

    def aic(term, data):
        r = smf.glm("n ~ " + cal + term, data, family=fam).fit()
        return float(r.aic), int(r.df_model)

    def qbins(x, k):
        return pd.qcut(x, k, duplicates="drop").astype(str)

    reg_t = pd.cut(S.TMAX, [-np.inf, 8, 14, 20, 23, 26, 29, 32, 35, 38, np.inf], right=False).astype(str)
    reg_p = pd.cut(S.pct, [0, 25, 50, 70, 80, 90, 95, 98, 100.0001], right=False).astype(str)
    a0 = aic("", S)[0]
    a1, a2 = aic(" + C(tb)", S.assign(tb=reg_t)), aic(" + C(pb)", S.assign(pb=reg_p))
    print(f"registrant's bins: degrees AIC {a1[0] - a0:.0f} below no-temperature model ({a1[1]} df), percentiles {a2[0] - a0:.0f} ({a2[1]} df); degrees better by {a2[0] - a1[0]:.0f}")
    print("   days per registrant bin, degrees:", reg_t.value_counts().sort_index().to_dict())
    print("   days per registrant bin, percentile:", reg_p.value_counts().sort_index().to_dict())
    for k in (10, 20):
        b1, b2, b3 = aic(" + C(tb)", S.assign(tb=qbins(S.TMAX, k))), aic(" + C(pb)", S.assign(pb=qbins(S.pct, k))), aic(" + C(ab)", S.assign(ab=qbins(S.anom, k)))
        print(f"{k} equal-count bins on each scale: degrees {b1[0] - a0:.0f}, percentiles {b2[0] - a0:.0f}, degrees from the city mean {b3[0] - a0:.0f}; degrees better than percentiles by {b2[0] - b1[0]:.0f}")
    for df_ in (4, 6):
        b1, b2 = aic(f" + cr(TMAX, df={df_})", S), aic(f" + cr(pct, df={df_})", S)
        print(f"natural spline {df_} df: degrees {b1[0] - a0:.0f}, percentiles {b2[0] - a0:.0f}; degrees better by {b2[0] - b1[0]:.0f}")
    W = S[S.pct >= 75]
    a0w = aic("", W)[0]
    for k in (5, 8):
        b1, b2 = aic(" + C(tb)", W.assign(tb=qbins(W.TMAX, k))), aic(" + C(pb)", W.assign(pb=qbins(W.pct, k)))
        print(f"hottest quarter of each city's days only, {k} equal-count bins: degrees {b1[0] - a0w:.0f}, percentiles {b2[0] - a0w:.0f}; degrees better by {b2[0] - b1[0]:.0f}")
    b1, b2 = aic(" + cr(TMAX, df=3)", W), aic(" + cr(pct, df=3)", W)
    print(f"hottest quarter, spline 3 df: degrees {b1[0] - a0w:.0f}, percentiles {b2[0] - a0w:.0f}; degrees better by {b2[0] - b1[0]:.0f}")
    H = S[S.city.isin(HOT4)]
    a0h = aic("", H)[0]
    b1, b2 = aic(" + C(tb)", H.assign(tb=qbins(H.TMAX, 10))), aic(" + C(pb)", H.assign(pb=qbins(H.pct, 10)))
    print(f"four hot cities only, 10 equal-count bins: degrees {b1[0] - a0h:.0f}, percentiles {b2[0] - a0h:.0f}; degrees better by {b2[0] - b1[0]:.0f}")

    print("\n== J. Exploratory heat-wave result (days two and later of a run) ==")

    def wave(city, y, thr=32.0, extra="", drop=None):
        d = derived(city, y)
        if drop:
            d = d[~d.year.isin(drop)]
        full = d.TMAX.reindex(pd.date_range(d.index.min(), d.index.max(), freq="D"))
        hot = (full >= thr).astype(int)
        run = (hot != hot.shift()).cumsum()
        pos = hot.groupby(run).cumsum()
        d["hotday"] = hot.reindex(d.index)
        d["later"] = ((hot == 1) & (pos >= 2)).astype(int).reindex(d.index)
        d["l1"] = d.TMAX.shift(1)
        for k in (15, 21, 27):
            d[f"s{k}"] = np.clip(d.TMAX - k, 0, None)
        d = d.dropna(subset=["l1", "TMIN"])
        a = alpha_ml(d, y)
        r = smf.glm(f"{y} ~ hotday + later + TMAX + s15 + s21 + s27 + {CAL}{extra}", d, family=sm.families.NegativeBinomial(alpha=a)).fit(cov_type="HC0")
        return {"log": float(r.params["later"]), "se": float(r.bse["later"])}, int(d.later.sum()), int(d.hotday.sum())

    for city, y, lab in (("new_york", "shoot", "New York shootings"), ("new_york", "n", "New York felony assaults"), ("chicago", "shoot", "Chicago shootings"), ("philadelphia", "shoot", "Philadelphia shootings"),
                         ("chicago", "n", "Chicago aggravated assaults"), ("philadelphia", "n", "Philadelphia aggravated assaults")):
        e, nl, nh = wave(city, y)
        print(f"{lab}: later days {nl} of {nh} hot days, ratio {s(e)}")
    print("New York shootings by threshold:", {thr: s(wave("new_york", "shoot", thr)[0]) for thr in (29, 30, 31, 32, 33, 34)})
    print("New York shootings, year-by-month terms:", s(wave("new_york", "shoot", extra=" + C(ym)")[0]), "| TMIN and yesterday's TMAX added:", s(wave("new_york", "shoot", extra=" + TMIN + l1")[0]),
          "| without 2020 and 2021:", s(wave("new_york", "shoot", drop=[2020, 2021])[0]))
    ws = [wave(c, "shoot")[0] for c in ("new_york", "chicago", "philadelphia")]
    print("three cities' shootings pooled:", s(pool(ws)), "| Chicago and Philadelphia only:", s(pool(ws[1:])))


if __name__ == "__main__":
    main()
