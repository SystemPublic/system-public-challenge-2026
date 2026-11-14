"""Analysis for further-subway-crime-per-ride-by-hour and further-subway-crime-per-million-repro, as registered."""
import json, math
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

D = Path(__file__).resolve().parents[2] / "data" / "derived" / "further_subway"
raw = json.loads((D / "raw.json").read_text())
BANDS = [("0-5", range(0, 5)), ("5-10", range(5, 10)), ("10-16", range(10, 16)), ("16-20", range(16, 20)), ("20-24", range(20, 24))]
BAND_OF = {h: b for b, r in BANDS for h in r}


def df(keys):
    rows = []
    for k in keys:
        rows += raw[k]
    d = pd.DataFrame(rows)
    for c in ("y", "m", "n", "rnd"):
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def period(d):
    p = pd.Series("other", index=d.index)
    p[d.y == 2019] = "2019"
    p[((d.y == 2025) & (d.m >= 10)) | ((d.y == 2026) & (d.m <= 9))] = "L12"
    p2 = p.copy(); p2[d.y == 2025] = "CY25"
    return p, p2


def prep(d, hcol="hh"):
    d = d.copy()
    d["hour"] = pd.to_numeric(d[hcol], errors="coerce")
    if "ky_cd" in d: d["ky_cd"] = pd.to_numeric(d["ky_cd"], errors="coerce")
    d["period"], d["period5"] = period(d)
    return d


def cp_ci(k, n, a=0.05):
    lo = stats.beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi


def pois_ci(c, a=0.05):
    lo = stats.chi2.ppf(a / 2, 2 * c) / 2 if c > 0 else 0.0
    return lo, stats.chi2.ppf(1 - a / 2, 2 * c + 2) / 2


def rate_ratio(n1, e1, n2, e2):
    """(n1/e1)/(n2/e2) with exact conditional binomial interval, exposures fixed."""
    est = (n1 / e1) / (n2 / e2)
    lo, hi = cp_ci(n1, n1 + n2)
    f = lambda p: (p / (1 - p)) * (e2 / e1) if 0 < p < 1 else (0 if p == 0 else float("inf"))
    return est, f(lo), f(hi)


def ratio_of_ratios(c, e_pairs_est):  # Wald on log scale
    pass


rid = pd.concat([df(["rid_t69i-h2me"]).assign(src="t69i"), df(["rid_wujg-7c2s"]).assign(src="wujg"), df(["rid_5wq4-mkjj"]).assign(src="5wq4")])
rid = prep(rid); rid["band"] = rid.hour.map(BAND_OF)


def exposures(pcol="period"):
    g = rid[rid[pcol].isin(["2019", "L12", "CY25"])].groupby([pcol, "band"]).n.sum() / 1e6
    return g


def counts(frames, pcol="period", drop_rnd=False, kyset=None, prem=None):
    d = df(frames); d = prep(d)
    tot = d.n.sum()
    missing = d[d.hour.isna()].n.sum()
    d = d[d.hour.notna()]
    if drop_rnd: d = d[d.rnd != 1]
    if kyset is not None: d = d[d.ky_cd.isin(kyset)]
    if prem is not None: d = d[d.prem_typ_desc.isin(prem)]
    d["band"] = d.hour.map(BAND_OF)
    return d.groupby([pcol, "band"]).n.sum(), tot, missing


def analyse(name, N, E, bands=("0-5", "5-10", "10-16", "16-20", "20-24"), per="L12"):
    res = {"name": name}
    r = {}
    for p in ("2019", per):
        for b in bands:
            n = int(N.get((p, b), 0)); e = E[(p, b)]
            lo, hi = pois_ci(n)
            r[(p, b)] = dict(n=n, e=e, rate=n / e, lo=lo / e, hi=hi / e)
    res["rates"] = {f"{p}|{b}": v for (p, b), v in r.items()}
    # pooled all bands
    for p in ("2019", per):
        n = sum(r[(p, b)]["n"] for b in bands); e = sum(r[(p, b)]["e"] for b in bands)
        lo, hi = pois_ci(n); r[(p, "all")] = dict(n=n, e=e, rate=n / e, lo=lo / e, hi=hi / e)
        res["rates"][f"{p}|all"] = r[(p, "all")]
    A = rate_ratio(r[(per, "0-5")]["n"], r[(per, "0-5")]["e"], r[(per, "10-16")]["n"], r[(per, "10-16")]["e"])
    A19 = rate_ratio(r[("2019", "0-5")]["n"], r[("2019", "0-5")]["e"], r[("2019", "10-16")]["n"], r[("2019", "10-16")]["e"])
    A2024 = rate_ratio(r[(per, "20-24")]["n"], r[(per, "20-24")]["e"], r[(per, "10-16")]["n"], r[(per, "10-16")]["e"])
    G = {b: rate_ratio(r[(per, b)]["n"], r[(per, b)]["e"], r[("2019", b)]["n"], r[("2019", b)]["e"]) for b in list(bands) + ["all"]}
    n0, n1, m0, m1 = r[(per, "0-5")]["n"], r[(per, "all")]["n"], r[("2019", "0-5")]["n"], r[("2019", "all")]["n"]
    # B = G[0-5]/G_all; the 0-5 counts are part of all; use all-except-0-5 for the variance, point from totals
    est = G["0-5"][0] / G["all"][0]
    se = math.sqrt(1 / n0 + 1 / m0 + 1 / max(n1 - n0, 1) + 1 / max(m1 - m0, 1))
    B = (est, est * math.exp(-1.96 * se), est * math.exp(1.96 * se))
    res.update(A=A, A_2019=A19, A_2024=A2024, G=G, B=B)
    return res


out = {}
SUBWAY = ["TRANSIT - NYC SUBWAY"]
KY = [101, 104, 105, 106, 107, 109, 110]
frames_sub = ["qgea-i56i_subway", "5uac-w243_subway"]
E = exposures()
N, tot, miss = counts(frames_sub, prem=SUBWAY)
out["primary"] = analyse("primary", N, E)
out["primary"]["dropped_missing_time"] = int(miss); out["primary"]["total_rows_count"] = int(tot)
# year descriptive series
d = prep(df(frames_sub)); d = d[d.hour.notna() & (d.prem_typ_desc == "TRANSIT - NYC SUBWAY")]; d["band"] = d.hour.map(BAND_OF)
cy = d.groupby(["y", "band"]).n.sum().unstack().fillna(0)
rd = rid.copy(); ey = rd.groupby(["y", "band"]).n.sum().unstack() / 1e6
out["year_series"] = {"counts": cy.to_dict("index"), "entries_m": ey.to_dict("index")}
# sensitivities
Nb, _, _ = counts(frames_sub, prem=SUBWAY + ["TRANSIT FACILITY (OTHER)"]); out["S1"] = analyse("S1 premise + transit facility other", Nb, E)
Nd, _, _ = counts(["qgea-i56i_district", "5uac-w243_district"]); out["S2"] = analyse("S2 transit_district not null", Nd, E)
Nr, _, _ = counts(frames_sub, drop_rnd=True, prem=SUBWAY); out["S3"] = analyse("S3 drop 00:00 and 12:00", Nr, E)
Nv, _, _ = counts(frames_sub, kyset=[101, 104, 105, 106], prem=SUBWAY); out["S4"] = analyse("S4 violent types", Nv, E)
E5 = exposures("period5")
N5, _, _ = counts(frames_sub, pcol="period5", prem=SUBWAY); out["S5"] = analyse("S5 calendar 2025", N5, E5, per="CY25")
# S6 shifted bands 22-4 vs 10-16
BANDS6 = {h: ("22-4" if (h >= 22 or h < 4) else ("10-16" if 10 <= h < 16 else "oth")) for h in range(24)}
def s6():
    dd = prep(df(frames_sub)); dd = dd[dd.hour.notna() & (dd.prem_typ_desc == "TRANSIT - NYC SUBWAY")]; dd["b"] = dd.hour.map(BANDS6)
    n = dd.groupby(["period", "b"]).n.sum()
    rr = rid.copy(); rr["b"] = rr.hour.map(BANDS6); e = rr.groupby(["period", "b"]).n.sum() / 1e6
    res = {}
    for p in ("2019", "L12"):
        res[p] = {b: dict(n=int(n[(p, b)]), e=e[(p, b)], rate=n[(p, b)] / e[(p, b)]) for b in ("22-4", "10-16")}
    res["A"] = rate_ratio(n[("L12", "22-4")], e[("L12", "22-4")], n[("L12", "10-16")], e[("L12", "10-16")])
    res["G"] = rate_ratio(n[("L12", "22-4")], e[("L12", "22-4")], n[("2019", "22-4")], e[("2019", "22-4")])
    return res
out["S6"] = s6()
# placebo
dp = prep(df(["qgea-i56i_nonsubway", "5uac-w243_nonsubway"])); dp = dp[dp.hour.notna()]; dp["band"] = dp.hour.map(BAND_OF)
Np = dp.groupby(["period", "band"]).n.sum()
n0, m0 = Np[("L12", "0-5")], Np[("2019", "0-5")]
n1 = sum(Np[("L12", b)] for b, _ in BANDS); m1 = sum(Np[("2019", b)] for b, _ in BANDS)
est = (n0 / m0) / (n1 / m1); se = math.sqrt(1 / n0 + 1 / m0 + 1 / (n1 - n0) + 1 / (m1 - m0))
out["placebo"] = dict(D=(est, est * math.exp(-1.96 * se), est * math.exp(1.96 * se)), counts={f"{p}|{b}": int(v) for (p, b), v in Np.items() if p in ("2019", "L12")})
# reproduction
y = pd.DataFrame(raw["yeek"])
y["month"] = pd.to_datetime(y.month); y["c"] = pd.to_numeric(y.felony_count); y["r"] = pd.to_numeric(y.crimes_per_million_riders)
def readings(rowsel, yrs, months, mean_monthly=False):
    res = {}
    for yr in yrs:
        s = y[rowsel & (y.month.dt.year == yr) & (y.month.dt.month.isin(months))]
        g = s.groupby("month").agg(c=("c", "sum"), r=("r", "sum"))
        riders = (g.c / g.r.replace(0, np.nan))
        res[yr] = float(g.r.mean()) if mean_monthly else float(g.c.sum() / riders.sum())
        res[f"{yr}_counts"] = int(g.c.sum()); res[f"{yr}_months"] = len(g)
    res["fall_pct"] = 100 * (1 - res[2025] / res[2021])
    return res
nov, dec = list(range(1, 12)), list(range(1, 13))
nyct = y.agency == "NYCT"
rep = {
 "R1_primary": readings(nyct, (2019, 2021, 2024, 2025), nov),
 "R2": readings(nyct, (2021, 2025), dec),
 "R3": readings(nyct, (2021, 2025), nov, True),
 "R4": readings(nyct & (y.police_force == "NYPD"), (2021, 2025), nov),
 "R5": readings(y.agency.notna(), (2021, 2025), nov),
 "R6": readings(y.agency.isin(["NYCT", "SIR"]), (2021, 2025), nov),
}
# NYPD complaint check Jan-Nov 2025 and 2021
dc = prep(df(frames_sub)); dc = dc[dc.prem_typ_desc == "TRANSIT - NYC SUBWAY"]
cc = {int(yr): int(dc[(dc.y == yr) & (dc.m <= 11)].n.sum()) for yr in (2019, 2021, 2024, 2025)}
ee = {int(yr): float(rid[(rid.y == yr) & (rid.m <= 11)].n.sum() / 1e6) for yr in (2019, 2021, 2024, 2025)}
rep["complaints_jan_nov"] = {"counts": cc, "entries_m": ee, "rate": {k: cc[k] / ee[k] for k in cc}}
out["repro"] = rep
class E_(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        return str(o)
(D / "results.json").write_text(json.dumps(out, indent=1, cls=E_, default=str))
print(json.dumps(out, indent=1, cls=E_)[:200])
