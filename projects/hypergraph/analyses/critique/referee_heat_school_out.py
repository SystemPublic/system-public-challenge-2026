"""Referee re-estimation for heat-school-out. Written by the blind referee, not the registrant.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_heat_school_out.py

It rebuilds the school-window series from the cached incident and victim queries and the cached
GHCN-Daily file with its own code (it imports nothing from analyses/heat_solutions), refits the
deciding model, and runs variants the registrant did not run. It reads the cache only, fetches
nothing, prints its results and writes no file.
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

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
SOC = ROOT / "data/cache/socrata"
INC = SOC / "5ucz-vwe8-67d988765288e6cac748a49b.json"
VIC = SOC / "833y-fsy8-3020a4737b900baf28c50ef9.json"
WX = ROOT / "data/cache/noaa/USW00094728.csv"
ATT = ROOT / "data/derived/graph/triads/absence_daily.csv"
REG = ROOT / "data/derived/heat_solutions/school_window_daily.csv"
START, END = "2006-01-01", "2026-08-31"

# First and last day of classes, typed again by the referee. June dates are keyed by the calendar year
# of the June. 2006-07 to 2018-19 were compared with the attendance file; 2019-20, 2020-21, 2021-22,
# 2025-26 and September 2026 were compared with the Department of Education calendars.
FIRST = {2006: "09-05", 2007: "09-04", 2008: "09-02", 2009: "09-09", 2010: "09-08", 2011: "09-08", 2012: "09-06",
         2013: "09-09", 2014: "09-04", 2015: "09-09", 2016: "09-08", 2017: "09-07", 2018: "09-05", 2019: "09-05",
         2020: "09-21", 2021: "09-13", 2022: "09-08", 2023: "09-07", 2024: "09-05", 2025: "09-04", 2026: "09-10"}
LAST = {2006: "06-28", 2007: "06-27", 2008: "06-26", 2009: "06-26", 2010: "06-28", 2011: "06-28", 2012: "06-27",
        2013: "06-26", 2014: "06-26", 2015: "06-26", 2016: "06-28", 2017: "06-28", 2018: "06-26", 2019: "06-26",
        2020: "06-26", 2021: "06-25", 2022: "06-27", 2023: "06-27", 2024: "06-26", 2025: "06-26", 2026: "06-26"}
SKIP = {("end", 2020), ("start", 2020), ("end", 2021)}
FORM = "out + t5 + trend_end + trend_start + C(dow) + wet + C(wy)"


# ---------------------------------------------------------------- data
def weather():
    w = pd.read_csv(WX, low_memory=False, usecols=["DATE", "TMAX", "TMIN", "PRCP"])
    w["DATE"] = pd.to_datetime(w["DATE"])
    w = w.set_index("DATE")
    return w[["TMAX", "TMIN", "PRCP"]] / 10.0


def stamps(path):
    r = pd.DataFrame(json.loads(path.read_text())["rows"])
    hh = r["t"].str.split(":").str[0].astype(int)
    mm = r["t"].str.split(":").str[1].astype(int)
    r["ts"] = pd.to_datetime(r["d"].str[:10]) + pd.to_timedelta(hh * 60 + mm, unit="m")
    return r


def base(inc, shooting_day=False):
    """Daily frame. With shooting_day, an incident before 06:00 is counted on the previous date."""
    d = pd.DataFrame(index=pd.date_range(START, END, freq="D")).join(weather())
    d["dow"], d["month"], d["year"], d["doy"] = d.index.day_of_week, d.index.month, d.index.year, d.index.day_of_year
    hol = USFederalHolidayCalendar().holidays(START, END)
    extra = pd.DatetimeIndex([f"{y}-{md}" for y in range(2006, 2027) for md in ("07-04", "12-31", "01-01")])
    d["hol"] = d.index.isin(hol.union(extra)).astype(int)
    d["wet"] = (d["PRCP"] >= 1.0).astype(int)
    d["t5"], d["tmin5"] = d["TMAX"] / 5.0, d["TMIN"] / 5.0
    d["t5_lag"] = d["t5"].shift(1)
    ts = inc["ts"]
    day = ((ts - pd.Timedelta(hours=6)) if shooting_day else ts).dt.normalize()
    h = ts.dt.hour

    def cnt(mask):
        return day[mask].value_counts().reindex(d.index).fillna(0).astype(int)
    d["n"] = cnt(np.ones(len(ts), bool))
    d["n_00_05"], d["n_06_14"], d["n_15_19"], d["n_20_23"] = cnt(h < 6), cnt((h >= 6) & (h < 15)), cnt((h >= 15) & (h < 20)), cnt(h >= 20)
    d["n_06_23"] = d["n"] - d["n_00_05"]
    return d


def window(d, half=42, skip=SKIP, days="weekday", shift=0, dedup=False, kinds=("end", "start"), first=FIRST, last=LAST, drop_hol=True):
    """Stacked windows around each transition. shift moves every transition by that many days into the
    term (negative) or into the recess (positive), for placebo transitions."""
    parts = []
    for y in range(2006, 2027):
        for kind in kinds:
            if (kind, y) in skip:
                continue
            t0 = pd.Timestamp(f"{y}-{(last if kind == 'end' else first)[y]}")
            t0 = t0 + pd.Timedelta(days=shift if kind == "end" else -shift)
            r = (d.index - t0).days
            k = d[np.abs(r) <= half].copy()
            if k.empty:
                continue
            k["rel"] = r[np.abs(r) <= half]
            k["kind"] = kind
            k["out"] = ((k["rel"] > 0) if kind == "end" else (k["rel"] < 0)).astype(int)
            k["wy"] = kind + str(y)
            parts.append(k)
    k = pd.concat(parts)
    k["date"] = k.index
    if days == "weekday":
        k = k[k["dow"] < 5]
    elif days == "weekend":
        k = k[k["dow"] >= 5]
    if drop_hol:
        k = k[k["hol"] == 0]
    k = k.dropna(subset=["TMAX"]).copy()
    if dedup:  # a day in two windows is kept in the window of the nearer transition
        k["absrel"] = k["rel"].abs()
        k = k.sort_values("absrel").drop_duplicates("date", keep="first")
    k["trend_end"] = np.where(k["kind"] == "end", k["rel"], 0) / 30.0
    k["trend_start"] = np.where(k["kind"] == "start", k["rel"], 0) / 30.0
    return k.sort_values(["date", "kind"]).reset_index(drop=True)


# ---------------------------------------------------------------- models
def fit(k, y="n", form=FORM, name="out", family="nb", cov="HC0", groups=None):
    alpha = None
    if family == "nb":
        try:
            ml = smf.negativebinomial(f"{y} ~ {form}", k).fit(disp=0, maxiter=300)
            a = float(ml.params["alpha"])
            alpha = a if np.isfinite(a) and a > 1e-4 else None
        except Exception:
            alpha = None
    fam = sm.families.NegativeBinomial(alpha=alpha) if alpha else sm.families.Poisson()
    kw = {"cov_type": cov}
    if cov == "cluster":
        kw["cov_kwds"] = {"groups": pd.factorize(k[groups])[0]}
    if cov == "nonrobust":
        kw = {}
    r = smf.glm(f"{y} ~ {form}", k, family=fam).fit(**kw)
    b, se = float(r.params[name]), float(r.bse[name])
    return {"irr": np.exp(b), "lo": np.exp(b - 1.96 * se), "hi": np.exp(b + 1.96 * se), "se": se, "z": b / se, "alpha": alpha, "n": int(len(k)), "events": int(k[y].sum())}


def show(label, o):
    print(f"  {label:<62s} {o['irr']:.3f} ({o['lo']:.3f} to {o['hi']:.3f})  z={o['z']:.2f}  days={o['n']}  events={o['events']}")


def main():
    inc, vic = stamps(INC), stamps(VIC)
    d = base(inc)
    k = window(d)

    print("1. Reproduction")
    reg = pd.read_csv(REG, parse_dates=["date"])
    m = k.merge(reg, on=["date", "kind"], suffixes=("", "_reg"))
    print(f"  rows mine {len(k)}, registrant {len(reg)}, matched {len(m)}; counts differ on {(m.n != m.n_reg).sum()} rows; out differs on {(m.out != m.out_reg).sum()} rows")
    print(f"  days out {int(k.out.sum())}; shootings {int(k.n.sum())}; dates in two windows {int(k.date.duplicated().sum())}")
    p = fit(k)
    show("registered model", p)
    print(f"  alpha {p['alpha']:.4f}; se {p['se']:.4f}; lower limit with 1.96: {p['lo']:.4f}; one-sided p {1 - __import__('scipy').stats.norm.cdf(p['z']):.4f}")
    show("window 21", fit(window(d, 21)))
    k["q_end"], k["q_start"] = k.trend_end ** 2, k.trend_start ** 2
    show("quadratic trends", fit(k, form=FORM + " + q_end + q_start"))
    for kind in ("end", "start"):
        show(f"{kind} of term only", fit(k[k.kind == kind], form=f"out + t5 + trend_{kind} + C(dow) + wet + C(wy)"))
    for b in ("n_00_05", "n_06_14", "n_15_19", "n_20_23"):
        show(f"hour block {b} (Poisson, as in exploratory.py)", fit(k, y=b, family="poisson"))

    print("\n2. Window width (registered model)")
    for h in (14, 21, 28, 35, 42, 49, 56, 63, 70):
        show(f"half-width {h} days", fit(window(d, h)))
    print("  without the days nearest the transition (42-day window)")
    for g in (3, 7, 10):
        show(f"  dropping |rel| <= {g}", fit(k[k.rel.abs() > g]))
    show("  dropping the 10 days before the last day (Regents period)", fit(k[~((k.kind == "end") & (k.rel >= -10) & (k.rel <= 0))]))

    print("\n3. Model family and standard errors (42 days)")
    show("Poisson, HC0", fit(k, family="poisson"))
    show("negative binomial, model-based errors", fit(k, cov="nonrobust"))
    show("negative binomial, HC3", fit(k, cov="HC3"))
    show("negative binomial, clustered by transition", fit(k, cov="cluster", groups="wy"))
    show("negative binomial, clustered by year", fit(k, cov="cluster", groups="year"))
    show("negative binomial, clustered by date", fit(k, cov="cluster", groups="date"))
    kd = window(d, dedup=True)
    show("each date once (nearer transition)", fit(kd))
    show("year terms in place of transition terms", fit(k, form="out + t5 + trend_end + trend_start + C(dow) + wet + C(year) + C(kind)"))
    k["out_tr_end"], k["out_tr_start"] = k.out * k.trend_end, k.out * k.trend_start
    show("separate slopes on each side of the transition", fit(k, form=FORM + " + out_tr_end + out_tr_start"))
    show("TMIN added", fit(k, form=FORM + " + tmin5"))
    k["t5sq"] = k.t5 ** 2
    show("TMAX squared and previous day's TMAX added", fit(k.dropna(subset=["t5_lag"]), form=FORM + " + t5sq + t5_lag"))
    show("without temperature", fit(k, form=FORM.replace("t5 + ", "")))

    print("\n4. Years")
    show("with the 2020 and 2021 transitions", fit(window(d, skip=set())))
    show("2006 to 2019 only", fit(k[k.year <= 2019]))
    show("2022 to 2026 only", fit(k[k.year >= 2022]))
    show("without the 2026 start window (no school days in it)", fit(k[k.wy != "start2026"]))
    lo = []
    for y in sorted(k.year.unique()):
        o = fit(k[k.year != y])
        lo.append((y, o["irr"], o["lo"]))
    a = pd.DataFrame(lo, columns=["year", "irr", "lo"])
    print(f"  leave one year out: estimate {a.irr.min():.3f} to {a.irr.max():.3f}; lower limit {a.lo.min():.3f} to {a.lo.max():.3f}; lower limit above 1.00 in {(a.lo > 1).sum()} of {len(a)}")
    print("   ", "  ".join(f"{int(r.year)}:{r.lo:.3f}" for r in a.itertuples()))

    print("\n5. School calendar")
    att = pd.read_csv(ATT, parse_dates=["date"])
    g = att.groupby("sy").date.agg(["min", "max"])
    bad = []
    for sy, r in g.iterrows():
        if r["min"].strftime("%m-%d") != FIRST[sy]:
            bad.append(("first", sy, str(r["min"].date()), FIRST[sy]))
        if r["max"].strftime("%m-%d") != LAST[sy + 1]:
            bad.append(("last", sy + 1, str(r["max"].date()), LAST[sy + 1]))
    print("  disagreements with the attendance file:", bad)
    # weekdays coded as school days on which the attendance file has no record (closures inside the term)
    sch = k[(k.out == 0) & (k.date >= "2006-09-05") & (k.date <= "2019-06-26")]
    closed = sch[~sch.date.isin(att.date)]
    closed = closed[~((closed.date >= "2014-06-17") & (closed.date <= "2014-06-26"))]  # the 2014 file ends early
    print(f"  school-side weekdays 2006-09 to 2019-06: {len(sch)}; with no attendance record: {len(closed)}")
    print("   ", closed.date.dt.strftime("%Y-%m-%d").tolist())
    cset = set(closed.date)
    k2 = k[(k.date >= "2006-09-05") & (k.date <= "2019-06-26")].copy()
    show("windows inside the attendance file, as registered", fit(k2))
    show("  closures dropped", fit(k2[~k2.date.isin(cset)]))
    k3 = k2.copy()
    k3.loc[k3.date.isin(cset), "out"] = 1
    show("  closures counted as out", fit(k3))
    for s in (-1, 1):
        f2 = {y: (pd.Timestamp(f"{y}-{v}") + pd.Timedelta(days=s)).strftime("%m-%d") for y, v in FIRST.items()}
        l2 = {y: (pd.Timestamp(f"{y}-{v}") + pd.Timedelta(days=s)).strftime("%m-%d") for y, v in LAST.items()}
        show(f"all transition dates moved by {s:+d} day", fit(window(d, first=f2, last=l2)))

    print("\n6. Season")
    kw = window(d, days="weekend")
    show("weekend days, same windows (school is out on both sides)", fit(kw))
    ka = window(d, days="all")
    ka["wkday"] = (ka.dow < 5).astype(int)
    ka["out_wk"] = ka.out * ka.wkday
    show("all days: out on weekends (main effect)", fit(ka, form=FORM + " + out_wk"))
    show("all days: extra effect of out on weekdays (interaction)", fit(ka, form=FORM + " + out_wk", name="out_wk"))
    print("  placebo transitions, 21-day windows that lie wholly in term or wholly in recess")
    show("  real transitions, 21 days", fit(window(d, 21)))
    for s in (-35, -28, -22, 22, 28, 35):
        show(f"  both transitions moved {abs(s)} days into the {'term' if s < 0 else 'recess'}", fit(window(d, 21, shift=s)))
    for kind in ("end", "start"):
        for s in (-28, 28):
            kk = window(d, 21, shift=s, kinds=(kind,))
            show(f"  {kind} only, moved 28 days into the {'term' if s < 0 else 'recess'}", fit(kk, form=f"out + t5 + trend_{kind} + C(dow) + wet + C(wy)"))
    k["jul4"] = ((k.month == 7) & (k.date.dt.day <= 8)).astype(int)
    lab = {y: pd.Timestamp(f"{y}-09-01") + pd.offsets.Week(weekday=0) if pd.Timestamp(f"{y}-09-01").dayofweek != 0 else pd.Timestamp(f"{y}-09-01") for y in range(2006, 2027)}
    k["pre_labor"] = [int(0 < (lab[dt.year] - dt).days <= 7) for dt in k.date]
    show("without 1 to 8 July and the week before Labor Day", fit(k[(k.jul4 == 0) & (k.pre_labor == 0)]))
    # same day of the year in and out of school: 1 to 14 September, first day moves between 2 and 13 September
    s = d[(d.month == 9) & (d.index.day <= 14) & (d.dow < 5) & (d.hol == 0) & (d.year != 2020)].dropna(subset=["TMAX"]).copy()
    s["out"] = [int(dt < pd.Timestamp(f"{dt.year}-{FIRST[dt.year]}")) for dt in s.index]
    s["dom"] = s.index.day
    s = s[s.index <= END]
    print(f"  1 to 14 September weekdays: {len(s)}, out {int(s.out.sum())}")
    show("1 to 14 September, day-of-month and year terms", fit(s, form="out + t5 + C(dom) + C(year) + C(dow) + wet"))
    show("1 to 14 September, linear day-of-month and year terms", fit(s, form="out + t5 + dom + C(year) + C(dow) + wet"))

    print("\n7. Shootings after midnight")
    ds = base(inc, shooting_day=True)
    ks = window(ds)
    show("shooting days 06:00 to 05:59, weekdays by shooting day", fit(ks))
    show("  window 21", fit(window(ds, 21)))
    show("  the 00:00 to 05:59 part of the shooting day", fit(ks, y="n_00_05", family="poisson"))
    show("  the 06:00 to 23:59 part", fit(ks, y="n_06_23", family="poisson"))
    show("calendar date, 06:00 to 23:59 only", fit(k, y="n_06_23"))
    show("calendar date, 00:00 to 05:59, without Mondays", fit(k[k.dow != 0], y="n_00_05", family="poisson"))
    show("calendar date, 00:00 to 05:59, TMIN added", fit(k, y="n_00_05", family="poisson", form=FORM + " + tmin5"))
    show("weekend dates, 00:00 to 05:59", fit(kw, y="n_00_05", family="poisson"))
    show("weekend dates, 06:00 to 23:59", fit(kw, y="n_06_23", family="poisson"))
    for s_ in (-28, 28):
        show(f"placebo moved 28 days into the {'term' if s_ < 0 else 'recess'}, 00:00 to 05:59, 21 days", fit(window(d, 21, shift=s_), y="n_00_05", family="poisson"))
    show("real transitions, 00:00 to 05:59, 21 days", fit(window(d, 21), y="n_00_05", family="poisson"))
    k["share_dummy"] = 1
    kk = k[k.n > 0]
    X = sm.add_constant(pd.get_dummies(kk[["out", "t5", "trend_end", "trend_start", "wet"]].assign(dow=kk.dow.astype(str), yr=kk.year.astype(str)), drop_first=True).astype(float))
    r = sm.GLM(np.column_stack([kk.n_00_05.values, (kk.n - kk.n_00_05).values]), X, family=sm.families.Binomial()).fit(cov_type="HC0")
    b, se = r.params["out"], r.bse["out"]
    print(f"  odds that a weekday shooting is before 06:00, out against school: {np.exp(b):.3f} ({np.exp(b - 1.96 * se):.3f} to {np.exp(b + 1.96 * se):.3f})")

    print("\n8. Victims by age and hour (archived file, to 2024)")
    vic["date"] = vic.ts.dt.normalize()
    vic["grp"] = np.where(vic.age == "<18", "u18", np.where(vic.age == "18-24", "a1824", np.where(vic.age.isin(["25-44", "45-64", "65+"]), "a25", "unk")))
    vic["early"] = (vic.ts.dt.hour < 6).astype(int)
    kv = k[k.date <= "2024-12-31"].copy()
    for gname in ("u18", "a1824", "a25"):
        for e, lab_ in ((1, "00:00 to 05:59"), (0, "06:00 to 23:59")):
            c = vic[(vic.grp == gname) & (vic.early == e)].groupby("date").size()
            kv["y"] = kv.date.map(c).fillna(0).astype(int).values
            show(f"victims {gname}, {lab_}", fit(kv, y="y", family="poisson"))
    vw = vic[vic.grp != "unk"].merge(kv[["date", "kind", "out", "t5", "dow", "year"]].drop_duplicates("date"), on="date")
    tab = vw.groupby(["grp", "out"]).early.agg(["sum", "count"])
    tab["share"] = tab["sum"] / tab["count"]
    print(tab.to_string())
    vw["u18"] = (vw.grp == "u18").astype(int)
    r = smf.glm("early ~ out * u18 + t5 + C(dow) + C(year)", vw, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(vw.date)[0]})
    for nm in ("out", "out:u18"):
        b, se = r.params[nm], r.bse[nm]
        print(f"  odds a victim is shot before 06:00, {nm}: {np.exp(b):.3f} ({np.exp(b - 1.96 * se):.3f} to {np.exp(b + 1.96 * se):.3f}) p={r.pvalues[nm]:.3f}")

    print("\n9. Where the excess sits")
    show("without 1 to 8 July only", fit(k[k.jul4 == 0]))
    show("without the week before Labor Day only", fit(k[k.pre_labor == 0]))
    show("00:00 to 05:59 without 1 to 8 July and the week before Labor Day", fit(k[(k.jul4 == 0) & (k.pre_labor == 0)], y="n_00_05", family="poisson"))
    for kind in ("end", "start"):
        kk = k[k.kind == kind]
        f = f"out + t5 + trend_{kind} + C(dow) + wet + C(wy)"
        show(f"{kind} only, dropping |rel| <= 10", fit(kk[kk.rel.abs() > 10], form=f))
        show(f"{kind} only, 00:00 to 05:59", fit(kk, y="n_00_05", family="poisson", form=f))
        show(f"{kind} only, 06:00 to 23:59", fit(kk, y="n_06_23", form=f))
    show("00:00 to 05:59 on Mondays (Sunday night)", fit(k[k.dow == 0], y="n_00_05", family="poisson", form=FORM.replace("C(dow) + ", "")))
    ks["schoolnight"] = (ks.dow < 4).astype(int)
    show("shooting day, 00:00 to 05:59 part, Monday to Thursday nights", fit(ks[ks.dow < 4], y="n_00_05", family="poisson"))
    show("shooting day, 00:00 to 05:59 part, Friday night", fit(ks[ks.dow == 4], y="n_00_05", family="poisson", form=FORM.replace("C(dow) + ", "")))
    show("shooting day, all hours, Monday to Thursday nights", fit(ks[ks.dow < 4]))
    for h in (21, 63):
        show(f"00:00 to 05:59, half-width {h}", fit(window(d, h), y="n_00_05", family="poisson"))
        show(f"06:00 to 23:59, half-width {h}", fit(window(d, h), y="n_06_23"))
    show("00:00 to 05:59, quadratic trends", fit(k, y="n_00_05", family="poisson", form=FORM + " + q_end + q_start"))
    show("00:00 to 05:59, clustered by year", fit(k, y="n_00_05", family="poisson", cov="cluster", groups="year"))
    # closures inside the term, leaving out the run of days before the last day that the attendance file lacks
    lastd = {y: pd.Timestamp(f"{y}-{v}") for y, v in LAST.items()}
    real = {dt for dt in cset if not (0 <= (lastd[dt.year] - dt).days <= 12 and dt.month == 6) or dt in {pd.Timestamp("2018-06-15")}}
    print(f"  closures outside the last 12 days of term: {len(real)}; attendance file lacks {len(cset) - len(real)} other days in the last 12 days of term")
    show("  2006-09 to 2019-06, those closures dropped", fit(k2[~k2.date.isin(real)]))
    k4 = k2.copy()
    k4.loc[k4.date.isin(real), "out"] = 1
    show("  2006-09 to 2019-06, those closures counted as out", fit(k4))
    ka["t5_wk"], ka["te_wk"], ka["ts_wk"], ka["wet_wk"] = ka.t5 * ka.wkday, ka.trend_end * ka.wkday, ka.trend_start * ka.wkday, ka.wet * ka.wkday
    show("all days, weekday-specific trends and weather: out x weekday", fit(ka, form=FORM + " + out_wk + t5_wk + te_wk + ts_wk + wet_wk", name="out_wk"))
    t = inc["ts"]
    print(f"  incident times exactly 00:00: {(t.dt.hour.eq(0) & t.dt.minute.eq(0)).mean():.4f}; on the hour: {t.dt.minute.eq(0).mean():.3f}; before 06:00: {(t.dt.hour < 6).mean():.3f}")
    print("  mean shootings per weekday in the 42-day window by days from the transition (end; start)")
    for kind in ("end", "start"):
        kk = k[k.kind == kind].copy()
        kk["bin"] = pd.cut(kk.rel, [-43, -29, -15, -8, 0, 7, 14, 28, 42])
        print("   ", kind, kk.groupby("bin", observed=True).agg(all=("n", "mean"), early=("n_00_05", "mean"), tmax=("TMAX", "mean")).round(2).to_dict("index"))

    print("\n10. The morning after a public holiday")
    hol_dates = set(d.index[d.hol == 1])
    k["after_hol"] = [int((dt - pd.Timedelta(days=1)) in hol_dates) for dt in k.date]
    a = k[k.after_hol == 1]
    print(f"  weekdays that follow a public holiday: {len(a)} ({int(a.out.sum())} out of school); mean shootings before 06:00 on them {a.n_00_05.mean():.2f}, on other days {k[k.after_hol == 0].n_00_05.mean():.2f}")
    j5 = k[(k.date.dt.month == 7) & (k.date.dt.day == 5)]
    print(f"  5 July weekdays: {len(j5)}; mean shootings before 06:00 {j5.n_00_05.mean():.2f}; all hours {j5.n.mean():.2f}")
    show("registered model without the day after a public holiday", fit(k[k.after_hol == 0]))
    show("  00:00 to 05:59", fit(k[k.after_hol == 0], y="n_00_05", family="poisson"))
    show("registered model with a term for the day after a holiday", fit(k, form=FORM + " + after_hol"))
    show("  window 21, without the day after a public holiday", fit(window(d, 21).pipe(lambda x: x[[(dt - pd.Timedelta(days=1)) not in hol_dates for dt in x.date]])))
    k["early_hol"] = k.n_00_05 * k.after_hol
    k["n_adj"] = k.n - k.early_hol
    show("shootings before 06:00 on the day after a holiday removed", fit(k, y="n_adj"))
    kv["after_hol"] = [int((dt - pd.Timedelta(days=1)) in hol_dates) for dt in kv.date]
    for gname in ("u18", "a1824", "a25"):
        c = vic[(vic.grp == gname) & (vic.early == 1)].groupby("date").size()
        kv["y"] = kv.date.map(c).fillna(0).astype(int).values
        show(f"victims {gname} before 06:00, without the day after a holiday", fit(kv[kv.after_hol == 0], y="y", family="poisson"))
    vw2 = vw[~vw.date.isin(set(kv.date[kv.after_hol == 1]))]
    r = smf.glm("early ~ out * u18 + t5 + C(dow) + C(year)", vw2, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(vw2.date)[0]})
    for nm in ("out", "out:u18"):
        b, se = r.params[nm], r.bse[nm]
        print(f"  without the day after a holiday, odds a victim is shot before 06:00, {nm}: {np.exp(b):.3f} ({np.exp(b - 1.96 * se):.3f} to {np.exp(b + 1.96 * se):.3f}) p={r.pvalues[nm]:.3f}")
    print(vw2.groupby(["grp", "out"]).early.agg(["sum", "count", "mean"]).round(3).to_string())
    reg10 = (k.kind == "end") & (k.rel >= -10) & (k.rel <= 0)
    show("without the day after a holiday and without the 10 days before the last day", fit(k[(k.after_hol == 0) & ~reg10]))
    show("  the same, shootings from 06:00 to 23:59", fit(k[(k.after_hol == 0) & ~reg10], y="n_06_23"))
    show("shooting days, without the 10 days before the last day", fit(ks[~((ks.kind == "end") & (ks.rel >= -10) & (ks.rel <= 0))]))
    show("without the day after a holiday, with the 2020 and 2021 transitions", fit(window(d, skip=set()).pipe(lambda x: x[[(dt - pd.Timedelta(days=1)) not in hol_dates for dt in x.date]])))
    show("without the day after a holiday, 2006 to 2019", fit(k[(k.after_hol == 0) & (k.year <= 2019)]))


if __name__ == "__main__":
    main()
