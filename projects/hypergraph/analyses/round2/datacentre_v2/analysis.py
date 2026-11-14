"""Analysis for further-datacentre-share-manhattan-v2, as registered."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data" / "derived" / "further"
OUT = ROOT / "data" / "derived" / "round2" / "datacentre_v2"
THR = 4.4
LIST = {"60 Hudson Street": "1001440040", "111 Eighth Avenue": "1007390001", "32 Sixth Avenue": "1001920001",
        "325 Hudson Street": "1005970062", "375 Pearl Street": "1001137501", "85 Tenth Avenue": "1006870029",
        "75 Broad Street": "1000290070", "33 Whitehall Street": "1000100014", "32 Old Slip": "1000350001", "150 Varick Street": "1005050001"}
rng = np.random.default_rng(20261113)
num = lambda s: pd.to_numeric(s, errors="coerce")

d = pd.read_csv(D / "ll84_mn_bx.csv", dtype=str)
d["yr"] = num(d.report_year).astype(int)
d["bbl"] = d.nyc_borough_block_and_lot.fillna("").str.replace(r"\D", "", regex=True)
d["elec"] = num(d.electricity_use_grid_purchase_1)
d["gfa"] = num(d.property_gfa_calculated).fillna(num(d.property_gfa_self_reported))
d["dcarea"] = num(d.data_center_gross_floor_area)
d["it"] = num(d.data_center_it_site_energy)
d["pue"] = num(d.data_center_pue)
d["B"] = d.borough.str.upper()
d["standalone"] = d.parent_property_id.fillna("").str.startswith("Not Applicable")
d["flagq"] = (d.alert_data_center_issue_with == "Possible Issue") | (d.estimated_values_energy == "Yes") | (d.estimated_data_flag == "Yes")

def mn(y, B="MANHATTAN"):
    return d[(d.yr == y) & (d.B == B)].copy()

def pick(y, B="MANHATTAN"):
    m = mn(y, B)
    m = m[m.elec.notna() & (m.elec >= 0)].copy()
    m["role"] = "other"; m["from_year"] = y
    info = {}
    for n, b in LIST.items():
        r = m[m.bbl == b]
        if len(r):
            m.loc[m.bbl == b, "role"] = "listed"; info[n] = (len(r), y)
        elif B == "MANHATTAN":
            for y2 in range(y - 1, 2021, -1):
                e = mn(y2); e = e[(e.bbl == b) & e.elec.notna() & (e.elec >= 0)]
                if len(e):
                    e = e.copy(); e["role"] = "listed"; e["from_year"] = y2; m = pd.concat([m, e]); info[n] = (len(e), y2); break
            else:
                info[n] = (0, None)
    if B == "MANHATTAN":
        m.loc[(m.dcarea > 0) & (m.role == "other"), "role"] = "flagged"
    return m, info

def office_pool(m, minarea=50000):
    p = m[(m.role == "other") & (m.largest_property_use_type == "Office") & (m.gfa >= minarea) & (m.elec > 0)
          & m.standalone & ~(m.dcarea > 0) & ~m.flagq & ~(m.it > 0)].copy()
    p["int"] = p.elec / p.gfa
    return p

def estimate(m, med, pue_lo=1.4, pue_hi=2.0, cap=True, use_rep_pue=False):
    m = m.copy()
    hasit = m.it > 0
    lo = m.it.where(hasit, 0) * pue_lo
    hi = m.it.where(hasit, 0) * pue_hi
    if use_rep_pue:
        rp = m.pue.where(m.pue.between(1.0, 3.0))
        lo = lo.where(rp.isna(), m.it.where(hasit, 0) * rp); hi = hi.where(rp.isna(), m.it.where(hasit, 0) * rp)
    if cap:
        lo = np.minimum(lo, m.elec); hi = np.minimum(hi, m.elec)
    m["A_lo"], m["A_hi"] = lo, hi
    ok = (m.gfa > 0)
    m["B"] = 0.0
    lst = (m.role == "listed") & ok
    m.loc[lst, "B"] = np.maximum(0, m.elec[lst] / m.gfa[lst] - med) * m.gfa[lst]
    m["S_lo"] = m.A_lo
    m["S_hi"] = np.where(m.role == "listed", np.maximum(m.A_hi, m.B), m.A_hi)
    return m

def shares(m, D2=None, D3=None):
    D1 = m.elec.sum()
    r = {"D1_kWh": D1, "S_lo_kWh": m.S_lo.sum(), "S_hi_kWh": m.S_hi.sum(), "A_lo_kWh": m.A_lo.sum(), "A_hi_kWh": m.A_hi.sum(), "B_kWh": m.B.sum(),
         "n_it_buildings": int((m.it > 0).sum())}
    for nm, den in (("D1", D1), ("D2", D2 * 1000 if D2 else None), ("D3", D3 * 1000 if D3 else None)):
        if den:
            for k in ("S_lo", "S_hi", "A_lo", "A_hi", "B"):
                r[f"{k}_over_{nm}_pct"] = 100 * r[f"{k}_kWh"] / den
    return r

def boot(m, n=2000):
    fixed = m[(m.role == "listed") | (m.it > 0)]
    oth = m[~((m.role == "listed") | (m.it > 0))]
    ev = oth.elec.values
    out = {"S_lo": [], "S_hi": []}
    lo, hi = fixed.S_lo.sum(), fixed.S_hi.sum(); Ff = fixed.elec.sum()
    for _ in range(n):
        i = rng.integers(0, len(oth), len(oth))
        den = Ff + ev[i].sum()
        out["S_lo"].append(100 * lo / den); out["S_hi"].append(100 * hi / den)
    return {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in out.items()}

# denominators
uer = pd.read_csv(D / "uer_mn.csv", dtype=str); uer["v"] = num(uer.value); uer["y"] = num(uer.year).astype(int)
nyc = pd.read_csv(OUT / "uer_nyc_total.csv", dtype=str); nyc["v"] = num(nyc.value); nyc["y"] = num(nyc.year).astype(int)
zj = pd.read_csv(D / "zonej_daily.csv"); zj["date"] = pd.to_datetime(zj.date)

def denominators(y):
    D2 = uer[(uer.y == y) & (uer.data_field == "2_nat_consumption")].v.sum()
    mn_tot = uer[(uer.y == y) & (uer.data_field == "3_nat_consumption")].v.sum()
    nyc_tot = nyc[nyc.y == y].v.sum()
    mn_share = mn_tot / nyc_tot
    zjy = zj[(zj.zone == "N.Y.C.") & (zj.date.dt.year == y)]
    zj_mwh = zjy.energy_mwh.sum()
    return {"D2_MWh": D2, "UER_mn_total_MWh": mn_tot, "UER_nyc_total_MWh": nyc_tot, "mn_share_of_nyc": mn_share,
            "zoneJ_MWh": zj_mwh, "zoneJ_days": int(zjy.date.nunique()), "D3_MWh": zj_mwh * mn_share, "nyc_zips": int(nyc[nyc.y == y].zip_code.nunique())}

res = {}
def run(y, **kw):
    m, info = pick(y)
    pool = office_pool(m, kw.pop("minarea", 50000))
    med = float(pool["int"].median())
    est = estimate(m, med, **kw)
    return m, info, pool, med, est

Y = 2024
den = denominators(Y); res["denominators"] = den
m, info, pool, med, est = run(Y)
res["listed_rows"] = info
res["median_office_kWh_per_ft2"] = med; res["office_pool_n"] = len(pool)
res["office_pool_int_quantiles"] = {q: float(pool["int"].quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}
P = shares(est, den["D2_MWh"], den["D3_MWh"])
P["boot95_D1"] = boot(est); P["n_rows_D1"] = len(est)
res["primary"] = P
cols = ["property_name", "address_1", "bbl", "from_year", "largest_property_use_type", "gfa", "elec", "it", "dcarea", "A_lo", "A_hi", "B", "S_lo", "S_hi"]
res["listed_table"] = est[est.role == "listed"][cols].sort_values("S_hi", ascending=False).to_dict("records")
res["it_table_nonlisted"] = est[(est.it > 0) & (est.role != "listed")][cols].sort_values("A_hi", ascending=False).to_dict("records")
res["listed_intensity"] = {r["address_1"]: (r["elec"] / r["gfa"] if r["gfa"] else None) for r in res["listed_table"]}

# placebo P_B
lst = est[(est.role == "listed") & (est.gfa > 0)]
listedB = lst.B.sum()
draws = []
pi = pool["int"].values
for _ in range(2000):
    tot = 0.0
    for g in lst.gfa.values:
        c = pool[(pool.gfa >= 0.75 * g) & (pool.gfa <= 1.25 * g)]
        if len(c):
            r = c.iloc[rng.integers(0, len(c))]
            tot += max(0, r["int"] - med) * r.gfa
    draws.append(100 * tot / P["D1_kWh"])
draws = np.array(draws)
lp = 100 * listedB / P["D1_kWh"]
res["placebo_B"] = {"listed_B_pct_D1": lp, "n_listed_rows": len(lst), "draw_mean": float(draws.mean()), "p2.5": float(np.percentile(draws, 2.5)),
                    "p97.5": float(np.percentile(draws, 97.5)), "percentile_of_listed": float((draws < lp).mean() * 100)}
# P_A Bronx
bm, _ = pick(Y, "BRONX")
res["placebo_A_bronx"] = {"n_rows": len(bm), "IT_buildings": int((bm.it > 0).sum()), "IT_kWh": float(bm.it.fillna(0).sum()), "D1_kWh": float(bm.elec.sum())}

# decision
chk = {"a_D1": P["S_hi_over_D1_pct"] < THR, "a_D2": P["S_hi_over_D2_pct"] < THR,
       "b": 1.0 <= P["S_lo_over_D1_pct"] <= 1.3, "c": 1.8 <= P["S_hi_over_D1_pct"] <= 3.5, "d": bool(lp > res["placebo_B"]["p97.5"])}
res["checks"] = {k: bool(v) for k, v in chk.items()}
res["refute_met"] = bool(P["S_hi_over_D1_pct"] >= THR and P["S_hi_over_D2_pct"] >= THR)
res["support_met"] = bool(all(chk.values()))

# sensitivities
sens = {}
def sh(y, **kw):
    mm, _, _, md, ee = run(y, **kw); dd = denominators(y)
    s = shares(ee, dd["D2_MWh"], dd["D3_MWh"]); s["median_office"] = md; return s
keys = ("S_lo_over_D1_pct", "S_hi_over_D1_pct", "S_lo_over_D2_pct", "S_hi_over_D2_pct", "S_lo_over_D3_pct", "S_hi_over_D3_pct", "A_lo_kWh", "A_hi_kWh", "B_kWh", "median_office", "n_it_buildings")
for name, (y, kw) in {"year_2023": (2023, {}), "uncapped": (Y, dict(cap=False)), "reported_pue": (Y, dict(use_rep_pue=True)),
                      "offices_25k": (Y, dict(minarea=25000))}.items():
    s = sh(y, **kw); sens[name] = {k: s[k] for k in keys if k in s}
# D1 without estimated/alert rows (numerator rows kept only if not flagged)
mm = m[~m.flagq]; e2 = estimate(mm, float(office_pool(mm)["int"].median()))
s = shares(e2, den["D2_MWh"], den["D3_MWh"]); sens["drop_flagged_rows"] = {k: s[k] for k in keys[:2] + ("n_it_buildings",)}
# area-proportional flagged buildings not otherwise allocated
fl = est[(est.role == "flagged") & ~(est.it > 0) & (est.gfa > 0)]
add = (np.minimum(fl.dcarea / fl.gfa, 1) * fl.elec).sum()
sens["flagged_area_proportional_added_to_S_hi"] = {"added_kWh": float(add), "S_hi_over_D1_pct": 100 * (P["S_hi_kWh"] + add) / P["D1_kWh"],
                                                   "S_hi_over_D2_pct": 100 * (P["S_hi_kWh"] + add) / (den["D2_MWh"] * 1000), "n_buildings": len(fl)}
res["sensitivity"] = sens
res["reverse_bound_R_D1"] = THR / P["S_hi_over_D1_pct"]; res["reverse_bound_R_D2"] = THR / P["S_hi_over_D2_pct"]
(OUT / "results.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: res[k] for k in ("denominators", "median_office_kWh_per_ft2", "office_pool_n", "office_pool_int_quantiles", "checks", "refute_met", "support_met", "placebo_B", "placebo_A_bronx", "reverse_bound_R_D1", "reverse_bound_R_D2", "listed_rows")}, indent=1, default=float))
print(json.dumps(P, indent=1, default=float))
print(json.dumps(sens, indent=1, default=float))
for r in res["listed_table"]: print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})
print(len(res["it_table_nonlisted"]), "non-listed IT rows; top 5:")
for r in res["it_table_nonlisted"][:6]: print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})
