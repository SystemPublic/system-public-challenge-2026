"""Referee re-estimation for heat-ac-shootings and heat-ac-heat-calls. Written by the blind referee.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_heat_ac.py

It rebuilds the district table, the district assignment of shootings and the daily series from the
cached queries, the cached GHCN-Daily files and the Health Department files with its own code. It
does not import analyses/heat_solutions. It reads the cache only, fetches nothing, prints its
results and writes no file.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
import statsmodels.api as sm
from pandas.tseries.holiday import USFederalHolidayCalendar
from patsy import dmatrix
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
SOC = ROOT / "data/cache/socrata"
NOAA = ROOT / "data/cache/noaa"
EHDP = ROOT / "data/derived/heat/ehdp"
DER = ROOT / "data/derived/heat_solutions"
SHOOT = "5ucz-vwe8-67d988765288e6cac748a49b.json"
VICTIMS = "833y-fsy8-3020a4737b900baf28c50ef9.json"
EMS = "76xm-jjuj-bb794c21be6fd14f4f0e3a13.json"
CAL = "C(dow) + C(month) + C(year) + hol + wet"
START, END = "2006-01-01", "2026-08-31"
BORO = {"MN": 1, "BX": 2, "BK": 3, "QN": 4, "SI": 5}


def show(label, o, extra=""):
    print(f"  {label:<58s} {o['b']:+.3f} ({o['lo']:+.3f} to {o['hi']:+.3f})  se {o['se']:.4f}  n {o.get('n', '')} {extra}")


# ------------------------------------------------------------------ inputs
def weather(sid="USW00094728"):
    w = pd.read_csv(NOAA / f"{sid}.csv", low_memory=False, usecols=["DATE", "TMAX", "TMIN", "PRCP"])
    w["DATE"] = pd.to_datetime(w["DATE"])
    w = w.set_index("DATE").asfreq("D")
    return w / 10.0


def calendar(sid="USW00094728"):
    d = pd.DataFrame(index=pd.date_range(START, END, freq="D")).join(weather(sid))
    d["dow"], d["month"], d["year"] = d.index.dayofweek, d.index.month, d.index.year
    h = set(USFederalHolidayCalendar().holidays(START, END))
    h |= {pd.Timestamp(f"{y}-{md}") for y in range(2006, 2027) for md in ("07-04", "12-31", "01-01")}
    d["hol"] = d.index.isin(list(h)).astype(int)
    d["wet"] = (d["PRCP"] >= 1.0).astype(int)
    d["t5"] = d["TMAX"] / 5.0
    d["ym"] = d["year"] * 100 + d["month"]
    return d.dropna(subset=["TMAX"])


def districts():
    a = pd.read_csv(EHDP / "hvi-nta-2020.csv")
    g = a.groupby("CDTACode").agg(ac=("PCT_HOUSEHOLDS_AC", "mean"), ac_sd=("PCT_HOUSEHOLDS_AC", "std"), income=("MEDIAN_INCOME", "mean"),
                                  surf=("SURFACE_TEMP", "mean"), black=("PCT_BLACK_POP", "mean")).reset_index()
    g["cd"] = [BORO[c[:2]] * 100 + int(c[2:]) for c in g["CDTACode"]]
    g = g[g["cd"] % 100 <= 18].sort_values("cd").reset_index(drop=True)
    g["low_ac"] = (g["ac"] < g["ac"].median()).astype(int)
    g["low_inc"] = (g["income"] < g["income"].median()).astype(int)
    return g


def locate(lat, lon):
    gj = json.loads((EHDP / "CD.geojson").read_text())
    geoms = [shapely.geometry.shape(f["geometry"]) for f in gj["features"]]
    codes = np.array([int(f["properties"]["GEOCODE"]) for f in gj["features"]])
    tree = shapely.STRtree(geoms)
    pts = shapely.points(lon, lat)
    i, j = tree.query(pts, predicate="within")
    out = np.zeros(len(lat), int)
    out[i[::-1]] = codes[j[::-1]]
    return out


# ------------------------------------------------------------------ models
def binom(d, a="low", b="high", x="t5", controls=CAL, cov="HC0", extra_x=None):
    k = d[(d[a] + d[b]) > 0]
    X = dmatrix(f"{x} + {controls}", k, return_type="dataframe")
    m = sm.GLM(np.column_stack([k[a].values, k[b].values]), X, family=sm.families.Binomial())
    r = m.fit(cov_type="HAC", cov_kwds={"maxlags": 7}) if cov == "HAC" else m.fit(cov_type=cov)
    names = [x] if isinstance(x, str) and "+" not in x else [s.strip() for s in x.split("+")]
    res = []
    for nme in names:
        bb, se = float(r.params[nme]), float(r.bse[nme])
        res.append({"b": bb, "lo": bb - 1.96 * se, "hi": bb + 1.96 * se, "se": se, "n": len(k)})
    res[0]["disp"] = float(r.pearson_chi2 / r.df_resid)
    return res[0] if len(res) == 1 else res


def piece(d, knot, a="low", b="high", controls=CAL):
    k = d.copy()
    k["below"] = np.minimum(k["TMAX"], knot) / 5
    k["above"] = np.clip(k["TMAX"] - knot, 0, None) / 5
    return binom(k, a, b, x="below + above", controls=controls)


def count_slope(d, y, fam="poisson"):
    X = dmatrix("t5 + " + CAL, d, return_type="dataframe")
    if fam == "poisson":
        r = sm.GLM(d[y].values, X, family=sm.families.Poisson()).fit(cov_type="HC0")
        alpha = None
    else:
        ml = sm.NegativeBinomial(d[y].values, X).fit(disp=0, maxiter=500, method="bfgs")
        alpha = float(ml.params["alpha"])
        r = sm.GLM(d[y].values, X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0")
    b, se = float(r.params["t5"]), float(r.bse["t5"])
    return {"rr": np.exp(b), "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se), "alpha": alpha}


def daily(ev, cal, cd, datecol="date"):
    m = ev.merge(cd[["cd", "low_ac", "low_inc"]], on="cd", how="inner")
    d = cal.copy()

    def cnt(mask):
        return m[mask].groupby(datecol).size().reindex(d.index).fillna(0).astype(int)
    d["low"], d["high"] = cnt(m.low_ac == 1), cnt(m.low_ac == 0)
    d["li_low"], d["li_high"] = cnt((m.low_ac == 1) & (m.low_inc == 1)), cnt((m.low_ac == 0) & (m.low_inc == 1))
    d["hi_low"], d["hi_high"] = cnt((m.low_ac == 1) & (m.low_inc == 0)), cnt((m.low_ac == 0) & (m.low_inc == 0))
    return d, m


def pooled(parts):
    w = np.array([1 / p["se"] ** 2 for p in parts])
    b = float(np.sum(w * np.array([p["b"] for p in parts])) / w.sum())
    se = float(1 / np.sqrt(w.sum()))
    return {"b": b, "lo": b - 1.96 * se, "hi": b + 1.96 * se, "se": se, "n": ""}


def variants(d, label, knots=(24, 27, 30), bins=((-50, 10), (10, 20), (20, 27), (27, 60))):
    print(f"\n{label}: variants of the primary contrast (low-AC minus high-AC, log rate ratio per 5 C)")
    p = binom(d)
    show("registered model, HC0", p, f"Pearson chi2/df {p['disp']:.2f}")
    show("HAC errors, 7 lags", binom(d, cov="HAC"))
    q = dict(p)
    s = p["se"] * np.sqrt(max(p["disp"], 1))
    q.update(se=s, lo=p["b"] - 1.96 * s, hi=p["b"] + 1.96 * s)
    show("model errors scaled by Pearson dispersion", q)
    show("year-by-month terms", binom(d, controls="C(dow) + C(ym) + hol + wet"))
    show("without 2020 and 2021", binom(d[~d.year.isin([2020, 2021])]))
    show("previous day's TMAX added", binom(d.assign(lag=d["t5"].shift(1)).dropna(subset=["lag"]), controls=CAL + " + lag"))
    li, hi = binom(d, "li_low", "li_high"), binom(d, "hi_low", "hi_high")
    show("within low-income half", li, f"events {int(d.li_low.sum())} / {int(d.li_high.sum())}")
    show("within high-income half", hi, f"events {int(d.hi_low.sum())} / {int(d.hi_high.sum())}")
    show("income-stratified, inverse-variance pooled", pooled([li, hi]))
    # income contrast within AC halves, and AC and income together
    show("INCOME contrast (low minus high income), all districts",
         binom(d.assign(a=d.li_low + d.li_high, b=d.hi_low + d.hi_high), "a", "b"))
    for knot in knots:
        lo, up = piece(d, knot)
        show(f"piecewise, below {knot} C", lo)
        show(f"piecewise, above {knot} C", up)
    for a, b in bins:
        k = d[(d.TMAX >= a) & (d.TMAX < b)]
        show(f"days with TMAX from {a} to {b} C", binom(k), f"events {int(k.low.sum())} / {int(k.high.sum())}")
    return p


# ------------------------------------------------------------------ shootings
def shootings(cd):
    print("=" * 100, "\nHEAT-AC-SHOOTINGS")
    inc = pd.DataFrame(json.loads((SOC / SHOOT).read_text())["rows"])
    print("incidents in the cached query:", len(inc))
    t = inc["t"].astype(str)
    unpadded = ~t.str.match(r"^\d\d:")
    print("times not zero-padded:", int(unpadded.sum()), "examples:", t[unpadded].head(3).tolist())
    bad = 0
    for v in t:
        try:
            int(v[:2])
        except ValueError:
            bad += 1
    print("times on which the registered line int(t[:2]) raises an error:", bad)
    inc["hour"] = t.str.split(":").str[0].astype(int)
    print("incidents whose hour differs between the registered and the changed line:", int((inc["hour"] != t.str[:2].astype(int)).sum()))
    vf = SOC / VICTIMS
    if vf.exists():
        vt = pd.DataFrame(json.loads(vf.read_text())["rows"])["t"].astype(str)
        print("victim file 833y-fsy8 (used by heat-school-out only): rows", len(vt), " times not zero-padded:", int((~vt.str.match(r"^\d\d:")).sum()),
              "examples:", vt[~vt.str.match(r"^\d\d:")].head(3).tolist())
    a, b = inc["lat"].astype(float).values, inc["lon"].astype(float).values
    print("coordinates missing:", int(np.isnan(a).sum() + 0), "/", int(np.isnan(b).sum()))
    ok = ~(np.isnan(a) | np.isnan(b))
    sw = ok & (a < 0) & (b > 0)
    plain = ok & (a > 0) & (b < 0)
    print("rows with 'lat' negative and 'lon' positive (swapped):", int(sw.sum()), " rows in the right order:", int(plain.sum()),
          " neither:", int((ok & ~sw & ~plain).sum()))
    print("rows in neither order:", list(zip(a[ok & ~sw & ~plain].tolist(), b[ok & ~sw & ~plain].tolist())))
    lat, lon = np.where(sw, b, a), np.where(sw, a, b)
    inbox = ok & (lat > 40.45) & (lat < 40.95) & (lon > -74.30) & (lon < -73.65)
    print("after correction, inside the city's bounding box:", int(inbox.sum()), "of", int(ok.sum()))
    inc = inc[ok].copy()
    inc["lat"], inc["lon"] = lat[ok], lon[ok]
    inc["swapped"] = sw[ok]
    inc["cd"] = locate(inc["lat"].values, inc["lon"].values)
    print("assigned to one of the 59 districts:", int(inc.cd.isin(cd.cd).sum()), " to no district or a park code:", int((~inc.cd.isin(cd.cd)).sum()))
    wrong = locate(inc["lon"].values, inc["lat"].values)
    print("assigned to any polygon if the correction is reversed:", int((wrong > 0).sum()))
    inc["boro"] = inc.cd // 100
    print("swapped rows by year (share):", inc.assign(y=inc["d"].str[:4]).groupby("y")["swapped"].mean().round(2).to_dict())
    inc["date"] = pd.to_datetime(inc["d"].str[:10])
    inc["sdate"] = inc["date"] - pd.to_timedelta((inc["hour"] < 6).astype(int), unit="D")
    cal = calendar()
    inc_c = inc[inc["date"].isin(cal.index)]
    d, m = daily(inc_c, cal, cd)
    print("incidents in districts on days with TMAX:", len(m), " share in the low-AC half:", round(float(m.low_ac.mean()), 3))
    reg = pd.read_csv(DER / "shootings_daily_by_ac_half.csv", index_col=0, parse_dates=True)
    j = d[["low", "high"]].join(reg[["low", "high"]], rsuffix="_reg", how="outer").fillna(-1)
    print("days on which my low/high counts differ from the registrant's file:", int(((j.low != j.low_reg) | (j.high != j.high_reg)).sum()), "of", len(j))
    p = variants(d, "Shootings, calendar day")
    print("  z against no difference:", round(p["b"] / p["se"], 2), " z against the half-carry value 0.0416:", round((p["b"] - 0.041573) / p["se"], 2),
          " D:", round((p["b"] / p["se"]) ** 2 - ((p["b"] - 0.041573) / p["se"]) ** 2, 2))
    for g in ("low", "high"):
        s = count_slope(d, g, "nb")
        print(f"  {g}-AC half own rate ratio per 5 C (negative binomial): {s['rr']:.3f} ({s['lo']:.3f} to {s['hi']:.3f})")
    show("May to September", binom(d[d.month.between(5, 9)]))
    show("October to April", binom(d[~d.month.between(5, 9)]))
    show("2006 to 2019", binom(d[d.year <= 2019]))
    show("2020 to 2026", binom(d[d.year >= 2020]))
    k = d.assign(late=(d.year >= 2020).astype(int))
    k["t5_late"] = k["t5"] * k["late"]
    show("difference between the periods (late minus early)", binom(k, x="t5 + t5_late")[1])
    for bname, bcode in (("Manhattan", 1), ("Bronx", 2), ("Brooklyn", 3), ("Queens", 4), ("Staten Island", 5)):
        dd, _ = daily(inc_c[inc_c.boro != bcode], cal, cd)
        show(f"without {bname}", binom(dd))
    for bname, bcode in (("Bronx", 2), ("Brooklyn", 3), ("Queens", 4), ("Manhattan", 1)):
        dd, _ = daily(inc_c[inc_c.boro == bcode], cal, cd)
        show(f"within {bname} only", binom(dd), f"events {int(dd.low.sum())} / {int(dd.high.sum())}")
    for sid, nm in (("USW00014732", "LaGuardia"), ("USW00094789", "JFK")):
        c2 = calendar(sid)
        dd, _ = daily(inc[inc["date"].isin(c2.index)], c2, cd)
        show(f"temperature at {nm}", binom(dd))
        lo, up = piece(dd, 27)
        show(f"  {nm}, piecewise above 27 C", up)
    # the shooting day from 06:00 to 05:59
    inc_s = inc[inc["sdate"].isin(cal.index)]
    ds, _ = daily(inc_s, cal, cd, datecol="sdate")
    print("\n  shootings from 00:00 to 05:59:", int((inc_c.hour < 6).sum()), "of", len(inc_c), f"({(inc_c.hour < 6).mean():.3f})")
    variants(ds, "Shootings, day from 06:00 to 05:59 (small-hours incidents counted on the previous date)")
    dn, _ = daily(inc_c[inc_c.hour >= 6], cal, cd)
    show("calendar day, incidents from 06:00 to 23:59 only", binom(dn))
    lo, up = piece(dn, 27)
    show("  the same, piecewise below 27 C", lo)
    show("  the same, piecewise above 27 C", up)
    dn, _ = daily(inc_s[inc_s.hour < 6], cal, cd, datecol="sdate")
    show("00:00 to 05:59 incidents on the PREVIOUS date's TMAX", binom(dn))
    dn, _ = daily(inc_c[inc_c.hour < 6], cal, cd)
    show("00:00 to 05:59 incidents on the same date's TMAX (registered)", binom(dn))
    # continuous district model: slopes by district on air conditioning and income
    rows = []
    for c, g in m.groupby("cd"):
        if len(g) < 150:
            continue
        y = g.groupby("date").size().reindex(cal.index).fillna(0).values
        X = dmatrix("t5 + " + CAL, cal, return_type="dataframe")
        r = sm.GLM(y, X, family=sm.families.Poisson()).fit(cov_type="HC0")
        rows.append({"cd": c, "slope": float(r.params["t5"]), "se": float(r.bse["t5"]), "n": len(g)})
    s = pd.DataFrame(rows).merge(cd, on="cd")
    s["ac10"], s["linc"] = (s.ac - s.ac.mean()) / 10, np.log(s.income) - np.log(s.income).mean()
    for nm, cols in (("air conditioning alone", ["ac10"]), ("income alone", ["linc"]), ("both", ["ac10", "linc"])):
        r = sm.WLS(s["slope"], sm.add_constant(s[cols]), weights=1 / s.se ** 2).fit(cov_type="HC1")
        print(f"  district slopes ({len(s)} districts) on {nm}: " + "; ".join(f"{c} {r.params[c]:+.3f} ({r.params[c] - 1.96 * r.bse[c]:+.3f} to {r.params[c] + 1.96 * r.bse[c]:+.3f})" for c in cols))
    return d


# ------------------------------------------------------------------ heat calls
def heat_calls(cd):
    print("=" * 100, "\nHEAT-AC-HEAT-CALLS")
    e = pd.DataFrame(json.loads((SOC / EMS).read_text())["rows"])
    e["ts"] = pd.to_datetime(e["dt"])
    e["date"] = e["ts"].dt.normalize()
    e["cdn"] = pd.to_numeric(e["cd"], errors="coerce")
    print("HEAT calls in the cached query:", len(e), " first:", e.ts.min(), " last:", e.ts.max())
    print("community district missing:", int(e.cdn.isna().sum()), " not one of the 59 districts:", int((~e.cdn.isin(cd.cd) & e.cdn.notna()).sum()))
    print("calls in September 2026, after the end of the calendar (31 August 2026):", int((e.date > END).sum()))
    hot = e.merge(calendar()[["TMAX"]], left_on="date", right_index=True)
    print("share of calls with no usable district, days below 30 C and days of 30 C or more:",
          round(float((~hot[hot.TMAX < 30].cdn.isin(cd.cd)).mean()), 3), round(float((~hot[hot.TMAX >= 30].cdn.isin(cd.cd)).mean()), 3))
    e = e.dropna(subset=["cdn"]).assign(cd=lambda x: x.cdn.astype(int))
    cal = calendar()
    cal = cal[cal.month.between(5, 9)]
    ee = e[e["date"].isin(cal.index)]
    d, m = daily(ee, cal, cd)
    print("calls in districts, May to September 2006 to 2026:", len(m), " share in the low-AC half:", round(float(m.low_ac.mean()), 3),
          " share of calls since 2006 that fall in May to September:", round(len(ee) / (e.date >= "2006-01-01").sum(), 3))
    print("calls by hour block (00-05, 06-11, 12-17, 18-23):", np.bincount(m.ts.dt.hour // 6, minlength=4).tolist())
    reg = pd.read_csv(DER / "heat_calls_daily_by_ac_half.csv", index_col=0, parse_dates=True)
    j = d[["low", "high"]].join(reg[["low", "high"]], rsuffix="_reg", how="outer").fillna(-1)
    print("days on which my low/high counts differ from the registrant's file:", int(((j.low != j.low_reg) | (j.high != j.high_reg)).sum()), "of", len(j))
    p = variants(d, "Heat calls", knots=(27, 30), bins=((27, 60), (30, 60)))
    y = 0.11246530985121782
    print("  z against no difference:", round(p["b"] / p["se"], 2), " z against the yardstick 0.112:", round((p["b"] - y) / p["se"], 2),
          " D:", round((p["b"] / p["se"]) ** 2 - ((p["b"] - y) / p["se"]) ** 2, 2))
    rr, ul, uh = 1 / 0.23, 0.139, 0.05
    print("  yardstick if a share h of calls come from homes:",
          {h: round(0.5 * np.log((1 + h * (rr - 1) * ul) / (1 + h * (rr - 1) * uh)), 3) for h in (1, 0.75, 0.5, 0.25, 0.15, 0.1)})
    for g in ("low", "high"):
        s = count_slope(d, g, "poisson")
        print(f"  {g}-AC half own rate ratio per 5 C, Poisson: {s['rr']:.3f} ({s['lo']:.3f} to {s['hi']:.3f})")
        try:
            s = count_slope(d, g, "nb")
            print(f"  {g}-AC half own rate ratio per 5 C, negative binomial (my fit, alpha {s['alpha']:.3f}): {s['rr']:.3f} ({s['lo']:.3f} to {s['hi']:.3f})")
        except Exception as ex:
            print(f"  {g}-AC half negative binomial failed: {type(ex).__name__}")
    low_m = [101, 102, 103, 104, 105, 106]
    dd, _ = daily(ee[~ee.cd.isin(low_m)], cal, cd)
    show("without Manhattan below 59th Street", binom(dd))
    dd, _ = daily(ee[ee.cd // 100 != 1], cal, cd)
    show("without Manhattan", binom(dd))
    for bname, bcode in (("Bronx", 2), ("Brooklyn", 3), ("Queens", 4), ("Staten Island", 5)):
        dd, _ = daily(ee[ee.cd // 100 != bcode], cal, cd)
        show(f"without {bname}", binom(dd))
    dd, _ = daily(ee[ee.ts.dt.hour.between(10, 19)], cal, cd)
    show("calls from 10:00 to 19:59 only", binom(dd))
    dd, _ = daily(ee[~ee.ts.dt.hour.between(10, 19)], cal, cd)
    show("calls from 20:00 to 09:59 only", binom(dd))
    dd, _ = daily(ee[ee.date.dt.dayofweek >= 5], cal, cd)
    show("Saturdays and Sundays only", binom(dd))
    for sid, nm in (("USW00014732", "LaGuardia"), ("USW00094789", "JFK")):
        c2 = calendar(sid)
        c2 = c2[c2.month.between(5, 9)]
        dd, _ = daily(e[e["date"].isin(c2.index)], c2, cd)
        show(f"temperature at {nm}", binom(dd))
    show("2006 to 2019", binom(d[d.year <= 2019]))
    show("2020 to 2026", binom(d[d.year >= 2020]))
    k = d.assign(tmin5=d.TMIN / 5).dropna(subset=["tmin5"])
    show("TMIN in place of TMAX", binom(k, x="tmin5"))
    # level: calls on hot days per day in each half
    h = d[d.TMAX >= 32]
    print(f"  days of 32 C or more: {len(h)}; calls per day low-AC half {h.low.mean():.2f}, high-AC half {h.high.mean():.2f}; share low {h.low.sum() / (h.low.sum() + h.high.sum()):.3f}")
    c = d[d.TMAX < 27]
    print(f"  days below 27 C: {len(c)}; share low {c.low.sum() / (c.low.sum() + c.high.sum()):.3f}")


def main():
    cd = districts()
    print("districts:", len(cd), " low-AC:", int(cd.low_ac.sum()), " median AC:", round(float(cd.ac.median()), 3),
          " mean AC low/high:", round(float(cd[cd.low_ac == 1].ac.mean()), 3), round(float(cd[cd.low_ac == 0].ac.mean()), 3))
    print("largest within-district standard deviation of the AC share across tabulation areas:", round(float(cd.ac_sd.max()), 3),
          " distinct AC values:", cd.ac.round(2).nunique())
    print("Spearman AC and income:", round(float(stats.spearmanr(cd.ac, cd.income)[0]), 3), " Pearson AC and log income:",
          round(float(np.corrcoef(cd.ac, np.log(cd.income))[0, 1]), 3), " Spearman AC and surface temperature:", round(float(stats.spearmanr(cd.ac, cd.surf)[0]), 3),
          " Spearman AC and percent Black:", round(float(stats.spearmanr(cd.ac, cd.black)[0]), 3))
    print("cross-table of low-AC by low-income districts:\n", pd.crosstab(cd.low_ac, cd.low_inc))
    reg = pd.read_csv(DER / "cd_table.csv")
    k = cd.merge(reg, on="cd", suffixes=("", "_reg"))
    print("districts whose low-AC flag differs from the registrant's table:", int((k.low_ac != k.low_ac_reg).sum()), "of", len(k))
    print("districts within 1 point of the median:", cd[(cd.ac - cd.ac.median()).abs() < 1][["cd", "ac", "low_ac"]].round(2).values.tolist())
    shootings(cd)
    heat_calls(cd)


if __name__ == "__main__":
    main()
