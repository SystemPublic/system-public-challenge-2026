"""Blind referee re-estimates for crz-storefront-vacancy and bridge-crz-ems-travel.

  python -m analyses.critique.referee_crz vacancy
  python -m analyses.critique.referee_crz ems

Written by the referee, independently of analyses/congestion/vacancy.py and ems_bridge.py
(the registrant's functions are called once each, only to check exact reproduction).
Reads the cached Socrata results and data/derived/congestion/; makes three new aggregate
queries to 76xm-jjuj (dispatch areas, yearly levels, zone ZIP check). Prints; writes nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from concord import socrata

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "congestion"
SEED = 20261113

# ---------------------------------------------------------------- areas (re-typed from the plan)
_z = list(range(10001, 10021)) + [10022, 10036, 10038] + list(range(10041, 10049)) + \
    [10055, 10060, 10080, 10081, 10087, 10090, 10095, 10098, 10099] + list(range(10101, 10124)) + \
    list(range(10150, 10180)) + [10199] + list(range(10256, 10287)) + [10008]
ZONE = {str(z) for z in _z}
NORTH = {"10021", "10023", "10024", "10025", "10028", "10065", "10069", "10075", "10128"}
BKLIC = {"11201", "11217", "11101", "11109"}


def area(z):
    z = str(z)[:5]
    return "crz" if z in ZONE else "north" if z in NORTH else "bklic" if z in BKLIC else "rest"


# ================================================================ vacancy
LABELS = {"2019 and 2020": 2019, "2020 and 2021": 2020, "2021 and 2022": 2021, "2022 and 2023": 2022,
          "2023": 2023, "2024": 2024, "2025": 2025}


def vac_rows():
    out = []
    for lab in LABELS:
        rows, _ = socrata.query_all(
            "92iy-9c3n", select="reporting_year, filing_due_date, bbl, borough_block_lot, zip_code, vacant_on_12_31, primary_business_activity",
            where=f"reporting_year='{lab}'", order=":id")
        out += rows
    df = pd.DataFrame(out)
    df["year"] = df.reporting_year.map(LABELS)
    df["due"] = df.filing_due_date.str[:10]
    df["area"] = df.zip_code.map(area)
    df["v"] = df.vacant_on_12_31.fillna("NA").replace({"Y": "YES"})
    return df


def did_pts(d, y, zone=("crz",), comp=("north", "bklic", "rest")):
    r = {}
    for nm, ar in (("z", zone), ("c", comp)):
        s = d[d.area.isin(ar)]
        a, b = s[s.year == y], s[s.year == y - 1]
        r[nm] = 100 * (a.vac.mean() - b.vac.mean())
    return r["z"] - r["c"], r["z"], r["c"]


def boot(d, y, cluster, zone=("crz",), comp=("north", "bklic", "rest"), draws=2000, seed=SEED):
    """Bootstrap of the DiD over clusters (lot or ZIP), resampled within zone and comparison."""
    d = d[d.year.isin([y - 1, y])]
    rng = np.random.default_rng(seed)
    arr = {}
    for nm, ar in (("z", zone), ("c", comp)):
        s = d[d.area.isin(ar)]
        g = s.groupby([cluster, "year"]).vac.agg(["sum", "size"]).unstack("year", fill_value=0)
        arr[nm] = g[[("sum", y), ("size", y), ("sum", y - 1), ("size", y - 1)]].to_numpy(float)
    bs = np.empty(draws)
    for i in range(draws):
        a = arr["z"][rng.integers(0, len(arr["z"]), len(arr["z"]))].sum(0)
        b = arr["c"][rng.integers(0, len(arr["c"]), len(arr["c"]))].sum(0)
        bs[i] = 100 * ((a[0] / a[1] - a[2] / a[3]) - (b[0] / b[1] - b[2] / b[3]))
    return float(np.quantile(bs, .025)), float(np.quantile(bs, .975)), float(bs.std())


def vacancy():
    df = vac_rows()
    print("== filings: rows by reporting year, due date, zone/outside and answer")
    df["zo"] = np.where(df.area == "crz", "zone", "outside")
    print(pd.crosstab([df.year, df.due, df.zo], df.v).to_string())
    print("rows with no ZIP by year:", df.zip_code.isna().groupby(df.year).sum().to_dict())
    main_due = df.groupby(["year", "due"]).size().reset_index(name="n").sort_values("n").groupby("year").tail(1)
    m = df.merge(main_due[["year", "due"]], on=["year", "due"])
    m = m[m.v.isin(["YES", "NO"])].copy()
    m["vac"] = (m.v == "YES").astype(int)
    m["lot"] = m.borough_block_lot.fillna(m.bbl)

    print("\n== V1 registered estimate, own code (main filing only)")
    for comp, nm in [(("north", "bklic", "rest"), "all outside"), (("north",), "north"), (("bklic",), "bklic"), (("rest",), "rest")]:
        e = did_pts(m, 2025, comp=comp)
        lo, hi, se = boot(m, 2025, "lot", comp=comp)
        print(f"{nm:12s} DiD {e[0]:+.2f} ({lo:+.2f} to {hi:+.2f}) se {se:.2f}; zone {e[1]:+.2f}, comparison {e[2]:+.2f}")
    from analyses.congestion import vacancy as reg
    mine = m.rename(columns={"zip_code": "zip_code"})[["year", "lot", "zip_code", "area", "vac"]]
    r = reg.did(mine, 2025)
    print("registrant's function on the same rows:", round(r["did_points"], 4), round(r["lo"], 4), round(r["hi"], 4))
    cnt = m.assign(zo=np.where(m.area == "crz", "zone", "outside")).groupby(["year", "zo"]).vac.agg(["sum", "size", "mean"])
    print(cnt.round(4).to_string())

    print("\n== V2 what the February filing is: lots in it that also appear in the June filing of the same year")
    for y in (2023, 2024, 2025):
        f = df[(df.year == y) & df.due.str[5:7].eq("02")]
        j = df[(df.year == y) & df.due.str[5:7].eq("06")]
        both = f.bbl.isin(set(j.bbl)).mean()
        jl = j[j.bbl.isin(set(f.bbl))]
        print(y, "Feb rows", len(f), "share of Feb rows whose lot is in the June filing", round(both, 3),
              "; June rows on those lots:", len(jl), "of which YES", int((jl.v == "YES").sum()))

    print("\n== V3 DiD with the February (all-vacant) filing added to the main filing, 2023 on")
    a = df[df.v.isin(["YES", "NO"]) & (df.due.str[5:7].isin(["02", "06"]) | (df.year <= 2022))].copy()
    a["vac"] = (a.v == "YES").astype(int)
    a["lot"] = a.borough_block_lot.fillna(a.bbl)
    for y in range(2020, 2026):
        e1 = did_pts(m, y)
        e2 = did_pts(a, y)
        print(y, f"main only {e1[0]:+.2f} (zone {e1[1]:+.2f}, out {e1[2]:+.2f});  with Feb filing {e2[0]:+.2f} (zone {e2[1]:+.2f}, out {e2[2]:+.2f})")
    lo, hi, se = boot(a, 2025, "lot")
    print(f"2025 with Feb filing: interval {lo:+.2f} to {hi:+.2f}, se {se:.2f}")
    for comp, nm in [(("north",), "north"), (("bklic",), "bklic")]:
        e = did_pts(a, 2025, comp=comp)
        lo, hi, se = boot(a, 2025, "lot", comp=comp)
        print(f"   with Feb filing vs {nm}: {e[0]:+.2f} ({lo:+.2f} to {hi:+.2f})")
    print(a.assign(zo=np.where(a.area == "crz", "zone", "outside")).groupby(["year", "zo"]).vac.agg(["sum", "size", "mean"]).round(4).to_string())

    print("\n== V4 lots present in the main filing of both 2024 and 2025")
    k = m[m.year.isin([2024, 2025])]
    keep = set(k[k.year == 2024].lot) & set(k[k.year == 2025].lot)
    b = k[k.lot.isin(keep)]
    e = did_pts(b, 2025)
    lo, hi, se = boot(b, 2025, "lot")
    print(f"balanced lots: DiD {e[0]:+.2f} ({lo:+.2f} to {hi:+.2f}); zone {e[1]:+.2f}, out {e[2]:+.2f}; rows kept {len(b)} of {len(k)}")
    for y in (2024, 2025):
        s = k[k.year == y]
        o = s[~s.lot.isin(keep)]
        print("  ", y, "rows on lots filing in only one year:", o.groupby(np.where(o.area == "crz", "zone", "outside")).vac.agg(["size", "mean"]).round(3).to_dict("index"))

    print("\n== V5 bootstrap over ZIP codes instead of tax lots; and without Roosevelt Island (10044)")
    lo, hi, se = boot(m, 2025, "zip_code")
    print(f"all outside, ZIP clusters: {did_pts(m, 2025)[0]:+.2f} ({lo:+.2f} to {hi:+.2f}) se {se:.2f}")
    lo, hi, se = boot(m, 2025, "zip_code", comp=("bklic",))
    print(f"bklic, ZIP clusters (4 ZIPs only): ({lo:+.2f} to {hi:+.2f})")
    x = m[m.zip_code != "10044"]
    print(f"without 10044: {did_pts(x, 2025)[0]:+.2f}")
    zz = m[(m.area == "crz") & m.year.isin([2024, 2025])].groupby(["zip_code", "year"]).vac.agg(["mean", "size"]).unstack()
    zz = zz[zz[("size", 2024)] >= 300]
    print("zone ZIPs with 300+ storefronts, change in vacancy share (points):")
    print((100 * (zz[("mean", 2025)] - zz[("mean", 2024)])).round(2).to_dict())

    print("\n== V6 allowance for the year-to-year movement of the DiD")
    pre = [did_pts(m, y)[0] for y in (2022, 2023, 2024)]
    e = did_pts(m, 2025)[0]
    _, _, se = boot(m, 2025, "lot")
    sd = float(np.std(pre, ddof=1))
    for lab, cf, s in [("against the mean of 2022-24", float(np.mean(pre)), np.sqrt(se ** 2 + sd ** 2 * (1 + 1 / 3))),
                       ("against zero, adding the year-to-year sd", 0.0, np.sqrt(se ** 2 + sd ** 2))]:
        print(f"{lab}: {e - cf:+.2f}, se {s:.2f}, normal 95% upper bound {e - cf + 1.96 * s:+.2f}, t(2) upper bound {e - cf + 4.30 * s:+.2f}")
    print("pre-toll DiDs 2022-24:", [round(v, 2) for v in pre], "sd", round(sd, 2))


# ================================================================ EMS
def is_peak(dow_mon0, hh):
    wk = dow_mon0 < 5
    return (wk & (hh >= 5) & (hh < 21)) | (~wk & (hh >= 9) & (hh < 21))


def ems_load(kind="ems"):
    df = pd.concat([pd.read_csv(DER / f"{kind}_{y}.csv") for y in range(2019, 2027)])
    df["d"] = pd.to_datetime(df["d"])
    df = df[~((df.d >= "2025-01-01") & (df.d < "2025-01-05"))].copy()
    df["peak"] = is_peak(df.d.dt.dayofweek, df.hh)
    df["month"] = df.d.dt.to_period("M").dt.to_timestamp()
    return df


def logratio(df, zone, comp, peak=True, value="travel"):
    q = df[df.peak == peak]
    z = q[q.area.isin(zone)].groupby("month")[[value, "n"]].sum()
    c = q[q.area.isin(comp)].groupby("month")[[value, "n"]].sum()
    return (np.log(z[value] / z.n) - np.log(c[value] / c.n)).dropna()


def fit(d, start="2025-01-01", pre="2023-01-01", to="2025-08-01", lags=3, formula="d ~ post + C(calm)", same_months=False):
    x = d[(d.index >= pre) & (d.index <= to)]
    f = pd.DataFrame({"d": x.values, "post": (x.index >= start).astype(int), "calm": x.index.month, "t": np.arange(len(x))}, index=x.index)
    if same_months:
        f = f[f.calm.isin(set(f[f.post == 1].calm))]
    mdl = smf.ols(formula, data=f).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(mdl.params["post"]), float(mdl.bse["post"])


def show(lab, b, se):
    print(f"{lab:58s} {100 * (np.exp(b) - 1):+.2f}% ({100 * (np.exp(b - 1.96 * se) - 1):+.2f} to {100 * (np.exp(b + 1.96 * se) - 1):+.2f}) log {b:+.4f} se {se:.4f}")


def ems():
    des = json.loads((DER / "ems_design.json").read_text())
    M, S = des["composed"]["mean_log"], des["composed"]["sd_log"]
    PROP = float(np.log(1 / 1.0575))
    df = ems_load()
    OUT = ("north", "bklic", "rest")
    pk = logratio(df, ("crz",), OUT, True)
    ov = logratio(df, ("crz",), OUT, False)

    print("== E1 registered endpoint, own code")
    b, se = fit(pk)
    show("peak, zone vs all outside, Jan-Aug 2025 vs 2023-24", b, se)
    tot = np.hypot(se, S)
    zc, zn, zp = (b - M) / tot, b / se, (b - PROP) / se
    print(f"z_chain {zc:.2f}  z_null {zn:.2f}  z_prop {zp:.2f}  D_null {zn**2 - zc**2:.2f}  D_prop {zp**2 - zc**2:.2f}")
    lo_e, hi_e = M - 1.96 * tot, M + 1.96 * tot
    lo_e = max(lo_e, PROP + se * np.sqrt(4))  # crude: D_prop >= 4 needs roughly this distance from proportional
    print(f"estimates that meet support_if at this se: about {100*(np.exp(lo_e)-1):+.1f}% to {100*(np.exp(hi_e)-1):+.1f}% (composed mean {100*(np.exp(M)-1):+.2f}%)")
    grid = np.linspace(-0.08, 0.04, 2401)
    ok = [(abs((g - M) / tot) < 1.96) and (((g - PROP) / se) ** 2 - ((g - M) / tot) ** 2 >= 4) for g in grid]
    g = grid[np.array(ok)]
    print(f"   exact support window: {100*(np.exp(g.min())-1):+.2f}% to {100*(np.exp(g.max())-1):+.2f}%")
    rng = np.random.default_rng(SEED)
    for lab, mu in [("no effect", 0.0), ("chain true", M), ("proportional", PROP), ("a rise of 1%", 0.01)]:
        dr = rng.normal(mu, se, 200000)
        okd = (np.abs((dr - M) / tot) < 1.96) & (((dr - PROP) / se) ** 2 - ((dr - M) / tot) ** 2 >= 4)
        print(f"   probability of 'confirmed' if the truth is {lab}: {okd.mean():.2f}")

    print("\n== E2 overnight and triple difference")
    bo, so = fit(ov)
    show("overnight, same estimator", bo, so)
    bt, st = fit((pk - ov).dropna())
    show("triple difference (peak minus overnight)", bt, st)
    print(f"triple difference against the composed prediction: z_chain {(bt - M) / np.hypot(st, S):.2f}; against no effect {bt / st:.2f}")
    for to, lab in [("2026-09-01", "to Sep 2026")]:
        show(f"peak {lab}", *fit(pk, to=to)); show(f"overnight {lab}", *fit(ov, to=to)); show(f"triple {lab}", *fit((pk - ov).dropna(), to=to))
    q = df[(df.d >= "2023-01-01") & (df.d < "2025-09-01")].assign(post=lambda x: x.d >= "2025-01-05", zone=lambda x: x.area == "crz")
    lv = q.groupby(["zone", "peak", "post"])[["travel", "n"]].sum()
    lv["mean_s"] = lv.travel / lv.n
    print("mean travel seconds, 2023-24 and Jan-Aug 2025 (not adjusted for season):")
    print(lv.mean_s.unstack("post").round(1).to_string())

    print("\n== E3 robustness of the peak endpoint")
    show("pre-period 2024 only", *fit(pk, pre="2024-01-01"))
    show("pre-period 2022-24", *fit(pk, pre="2022-01-01"))
    show("pre-period 2023-24, linear trend added", *fit(pk, formula="d ~ post + C(calm) + t"))
    show("Jan-Aug months only in both periods, no month terms", *fit(pk, formula="d ~ post", same_months=True))
    show("HAC 6 lags", *fit(pk, lags=6))
    show("vs rest of city only", *fit(logratio(df, ("crz",), ("rest",), True)))
    show("vs north", *fit(logratio(df, ("crz",), ("north",), True)))
    show("vs bklic", *fit(logratio(df, ("crz",), ("bklic",), True)))
    show("overnight, pre-period 2024 only", *fit(ov, pre="2024-01-01"))
    show("overnight, linear trend added", *fit(ov, formula="d ~ post + C(calm) + t"))
    show("overnight, vs north", *fit(logratio(df, ("crz",), ("north",), False)))
    show("triple, pre-period 2024 only", *fit((pk - ov).dropna(), pre="2024-01-01"))
    show("triple, linear trend added", *fit((pk - ov).dropna(), formula="d ~ post + C(calm) + t"))
    hi = df[df.sev == "hi"]; lo = df[df.sev == "lo"]
    show("life-threatening, peak", *fit(logratio(hi, ("crz",), OUT, True)))
    show("life-threatening, overnight", *fit(logratio(hi, ("crz",), OUT, False)))
    show("lower priority, peak", *fit(logratio(lo, ("crz",), OUT, True)))
    show("lower priority, overnight", *fit(logratio(lo, ("crz",), OUT, False)))
    show("total response time, peak", *fit(logratio(df, ("crz",), OUT, True, "response")))
    show("total response time, overnight", *fit(logratio(df, ("crz",), OUT, False, "response")))
    show("dispatch time, peak", *fit(logratio(df, ("crz",), OUT, True, "dispatch")))
    # incident counts
    qq = df[df.peak]
    nz = np.log(qq[qq.area == "crz"].groupby("month").n.sum()) - np.log(qq[qq.area != "crz"].groupby("month").n.sum())
    show("number of incidents, peak, zone vs outside", *fit(nz))
    qq = df[~df.peak]
    nz = np.log(qq[qq.area == "crz"].groupby("month").n.sum()) - np.log(qq[qq.area != "crz"].groupby("month").n.sum())
    show("number of incidents, overnight, zone vs outside", *fit(nz))

    print("\n== E4 false starts: the same 8-against-24-month estimator at every pre-toll start date")
    ests = []
    for s in pd.date_range("2021-01-01", "2024-05-01", freq="MS"):
        sub = pk[pk.index < "2025-01-01"]
        pre = s - pd.DateOffset(months=24)
        to = s + pd.DateOffset(months=7)
        if pre < sub.index.min():
            continue
        bb, ss = fit(sub, start=s, pre=pre, to=to)
        ests.append((s, bb, ss))
    e = pd.DataFrame(ests, columns=["start", "b", "se"])
    print(f"{len(e)} false starts 2021-10 to 2024-05: sd of estimates {e.b.std():.4f}, mean HAC se {e.se.mean():.4f}, range {e.b.min():+.4f} to {e.b.max():+.4f}")
    e2 = e[e.start >= "2023-01-01"]
    print(f"   starts in 2023-24 only ({len(e2)}): sd {e2.b.std():.4f}, range {e2.b.min():+.4f} to {e2.b.max():+.4f}")
    ests = []
    tr = (pk - ov).dropna()
    for s in pd.date_range("2023-01-01", "2024-05-01", freq="MS"):
        sub = tr[tr.index < "2025-01-01"]
        bb, ss = fit(sub, start=s, pre=s - pd.DateOffset(months=24), to=s + pd.DateOffset(months=7))
        ests.append(bb)
    print(f"   triple difference, starts in 2023-24: sd {np.std(ests, ddof=1):.4f}, range {min(ests):+.4f} to {max(ests):+.4f}")
    ests = []
    for s in pd.date_range("2023-01-01", "2024-05-01", freq="MS"):
        sub = ov[ov.index < "2025-01-01"]
        bb, ss = fit(sub, start=s, pre=s - pd.DateOffset(months=24), to=s + pd.DateOffset(months=7))
        ests.append(bb)
    print(f"   overnight, starts in 2023-24: sd {np.std(ests, ddof=1):.4f}, range {min(ests):+.4f} to {max(ests):+.4f}")

    print("\n== E5 zone by dispatch area (Manhattan M1-M3) instead of ZIP")
    rows, src = socrata.query_all(
        "76xm-jjuj",
        select=("date_trunc_ym(incident_datetime) as m, date_extract_dow(incident_datetime) as dow, date_extract_hh(incident_datetime) as hh, "
                "incident_dispatch_area as da, count(*) as n, sum(incident_travel_tm_seconds_qy) as travel"),
        where=("incident_datetime >= '2023-01-01T00:00:00' and incident_datetime < '2026-10-01T00:00:00' and valid_incident_rspns_time_indc='Y' "
               "and borough='MANHATTAN' and incident_dispatch_area in ('M1','M2','M3') "
               "and not (incident_datetime >= '2025-01-01T00:00:00' and incident_datetime < '2025-01-05T00:00:00')"),
        group="m, dow, hh, da", order="m, dow, hh, da")
    print("query fetched", src["fetched"], "rows", len(rows))
    da = pd.DataFrame(rows).astype({"dow": int, "hh": int, "n": float, "travel": float})
    da["month"] = pd.to_datetime(da.m)
    da["peak"] = is_peak((da.dow + 6) % 7, da.hh)   # Socrata dow: Sunday = 0
    city = df[df.d >= "2023-01-01"].groupby(["month", "peak"])[["travel", "n"]].sum()
    zn = da.groupby(["month", "peak"])[["travel", "n"]].sum()
    zip_zone = df[(df.d >= "2023-01-01") & (df.area == "crz")].groupby(["month", "peak"])[["travel", "n"]].sum()
    print("incidents 2023-24, zone by ZIP", int(zip_zone.loc[:"2024-12-01"].n.sum()), "; by dispatch area", int(zn.loc[:"2024-12-01"].n.sum()))
    out = city - zn
    dd = (np.log(zn.travel / zn.n) - np.log(out.travel / out.n)).unstack("peak")
    show("dispatch-area zone, peak", *fit(dd[True]))
    show("dispatch-area zone, overnight", *fit(dd[False]))
    show("dispatch-area zone, triple", *fit(dd[True] - dd[False]))
    for a in ("M1", "M2", "M3"):
        z1 = da[da.da == a].groupby(["month", "peak"])[["travel", "n"]].sum()
        d1 = (np.log(z1.travel / z1.n) - np.log(out.travel / out.n)).unstack("peak")
        show(f"   {a} peak", *fit(d1[True])); show(f"   {a} overnight", *fit(d1[False]))

    print("\n== E6 levels by year, all hours, citywide (valid incidents unless stated)")
    rows, _ = socrata.query_all(
        "76xm-jjuj",
        select=("date_extract_y(incident_datetime) as y, valid_incident_rspns_time_indc as v, count(*) as n, count(incident_travel_tm_seconds_qy) as nt, "
                "count(zipcode) as nz, sum(incident_travel_tm_seconds_qy) as t, sum(incident_response_seconds_qy) as r, sum(dispatch_response_seconds_qy) as dsp, "
                "sum(case(incident_travel_tm_seconds_qy=0,1,true,0)) as zero, sum(case(incident_travel_tm_seconds_qy>1800,1,true,0)) as long, "
                "sum(case(incident_travel_tm_seconds_qy<=300,1,true,0)) as short, sum(case(held_indicator='Y',1,true,0)) as held, "
                "sum(case(initial_severity_level_code in ('1','2','3'),1,true,0)) as hi"),
        where="incident_datetime >= '2019-01-01T00:00:00'", group="y, v", order="y, v")
    t = pd.DataFrame(rows)
    for c in t.columns[2:]:
        t[c] = t[c].astype(float)
    tot_n = t.groupby("y").n.transform("sum")
    t["invalid_share_of_year"] = np.where(t.v == "N", t.n / tot_n, np.nan)
    t["travel_s"], t["dispatch_s"], t["response_s"] = t.t / t.nt, t.dsp / t.n, t.r / t.n
    for c in ("nt", "nz", "zero", "long", "short", "held", "hi"):
        t[c + "_share"] = t[c] / t.n
    v = t[t.v == "Y"].set_index("y")
    print(v[["n", "travel_s", "dispatch_s", "response_s", "nt_share", "nz_share", "zero_share", "short_share", "long_share", "held_share", "hi_share"]].round(3).to_string())
    print("share of all incidents flagged invalid:", t[t.v == "N"].set_index("y").invalid_share_of_year.round(3).to_dict())
    cm = df.groupby("month")[["travel", "n"]].sum()
    s = np.log(cm.travel / cm.n)
    print("citywide monthly mean travel time: largest month-to-month log changes since 2022:",
          s[s.index >= "2022-01-01"].diff().abs().sort_values().tail(3).round(3).to_dict())
    print("12-month log change by half-year:", s.diff(12)[s.index >= "2023-01-01"].resample("6MS").mean().round(3).to_dict())

    print("\n== E7 link 2 (elasticity) and the composed prediction")
    sp = pd.read_csv(ROOT / "data/derived/mobility/crz_speeds_monthly.csv")
    sp["month"] = pd.to_datetime(sp.month)
    w = sp.pivot(index="month", columns="area", values="speed")
    x = pd.DataFrame({"d": pk, "s": np.log(w["CBD"] / w["Greater NYC"])}).dropna()
    x = x[x.index < "2025-01-01"]
    x["calm"] = x.index.month
    for lab, sub in [("Oct 2019 - Dec 2024 (registered)", x), ("without Mar 2020 - Jun 2021", x[(x.index < "2020-03-01") | (x.index > "2021-06-01")]),
                     ("2022-24", x[x.index >= "2022-01-01"]), ("2023-24", x[x.index >= "2023-01-01"])]:
        mm = smf.ols("d ~ s + C(calm)", data=sub).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        print(f"   {lab:32s} slope {mm.params['s']:+.3f} (se {mm.bse['s']:.3f}) n {int(mm.nobs)}  sd of log speed ratio {sub.s.std():.3f}")
    xo = pd.DataFrame({"d": ov, "s": np.log(w["CBD"] / w["Greater NYC"])}).dropna()
    xo = xo[xo.index < "2025-01-01"]; xo["calm"] = xo.index.month
    mm = smf.ols("d ~ s + C(calm)", data=xo).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    print(f"   overnight EMS ratio on the same speed ratio (placebo outcome): slope {mm.params['s']:+.3f} (se {mm.bse['s']:.3f})")
    rng = np.random.default_rng(SEED)
    n = 200000
    ls = rng.normal(np.log(1 / 1.0575), (np.log(1.0862) - np.log(1.0295)) / 3.92, n)
    for lab, trunc in [("exponent truncated at 0 (as registered)", True), ("exponent not truncated", False)]:
        ex = rng.normal(des["exponent"]["mean"], des["exponent"]["sd"], n)
        if trunc:
            while (ex < 0).any():
                ex[ex < 0] = rng.normal(des["exponent"]["mean"], des["exponent"]["sd"], (ex < 0).sum())
        c = ex * ls
        print(f"   composed, {lab}: mean {100*(np.exp(c.mean())-1):+.2f}%, median {100*(np.exp(np.median(c))-1):+.2f}%, "
              f"95% {100*(np.exp(np.quantile(c,.025))-1):+.2f} to {100*(np.exp(np.quantile(c,.975))-1):+.2f}, sd_log {c.std():.4f}")

    print("\n== E8 lives per year under each measured change (registrant's inputs, referee's draws)")
    ad = json.loads((DER / "arrest_design.json").read_text())
    N, resp, tsh = ad["zone_peak_attended_arrests_per_year_2023_24"], ad["mean_response_min_zone_peak"], ad["travel_share"]
    lor = rng.normal(np.log(1.12), (np.log(1.24) - np.log(1.02)) / 3.92, n)
    base = rng.uniform(0.03, 0.10, n)
    br, sr = fit(logratio(df, ("crz",), OUT, True, "response"))
    print(f"   attended arrests {N:.0f}/yr, mean response {resp:.2f} min, travel share {tsh:.2f}")
    for lab, mu, sd, share in [("composed prediction", M, S, tsh), ("peak DiD, travel (registered endpoint)", b, se, tsh),
                               ("triple difference, travel", bt, st, tsh), ("peak DiD, total response time", br, sr, 1.0),
                               ("no effect", 0.0, se, tsh)]:
        ch = rng.normal(mu, sd, n)
        L = N * base * (1 - base) * lor * (-(np.exp(ch) - 1) * resp * share)
        ql = np.quantile(L, [.025, .5, .975])
        print(f"   {lab:40s} {ql[1]:+.2f} ({ql[0]:+.2f} to {ql[2]:+.2f})  seconds saved {-(np.exp(mu)-1)*resp*share*60:+.1f}")
    at = pd.DataFrame(ad["table"])
    print(at[(at.zone) & (at.peak) & (at.year >= 2023)][["year", "n", "attended", "dead", "share_dead_of_attended", "mean_response_s"]].round(3).to_string())


if __name__ == "__main__":
    {"vacancy": vacancy, "ems": ems}[sys.argv[1]]()
