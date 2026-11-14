"""Analysis for further-datacentre-share-manhattan, as registered (claims/registered/further-datacentre-share-manhattan.json)."""
import json, re
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "further"
THR = 4.4
LIST = {  # name -> BBL (digits)
 "60 Hudson Street": "1001440040", "111 Eighth Avenue": "1007390001", "32 Sixth Avenue": "1001920001",
 "325 Hudson Street": "1005970062", "375 Pearl Street": "1001137501", "85 Tenth Avenue": "1006870029",
 "75 Broad Street": "1000290070", "33 Whitehall Street": "1000100014", "32 Old Slip": "1000350001",
 "150 Varick Street": "1005050001"}
rng = np.random.default_rng(20261112)

d = pd.read_csv(D / "ll84_mn_bx.csv", dtype=str)
num = lambda s: pd.to_numeric(s, errors="coerce")
d["yr"] = num(d.report_year).astype(int)
d["bbl"] = d.nyc_borough_block_and_lot.fillna("").str.replace(r"\D", "", regex=True)
d["elec"] = num(d.electricity_use_grid_purchase_1)
d["elec2"] = num(d.electricity_use_grid_purchase_2)
d["gfa"] = num(d.property_gfa_calculated).fillna(num(d.property_gfa_self_reported))
d["dcarea"] = num(d.data_center_gross_floor_area)
d["it"] = num(d.data_center_it_site_energy)
d["pue"] = num(d.data_center_pue)
d["lab"] = num(d.laboratory_gross_floor_area)
d["B"] = d.borough.str.upper()
d["standalone"] = d.parent_property_id.fillna("").str.startswith("Not Applicable")
d["flagq"] = (d.alert_data_center_issue_with == "Possible Issue") | (d.estimated_values_energy == "Yes") | (d.estimated_data_flag == "Yes")

uer = pd.read_csv(D / "uer_mn.csv", dtype=str)
uer["v"] = num(uer.value)
uer["y"] = num(uer.year).astype(int)

def mn(y, B="MANHATTAN"):
    return d[(d.yr == y) & (d.B == B)].copy()

def pick(y, drop60=False, listonly=False, nonflagq=False, col="elec", parent_ok=False):
    """Return (rows table, notes). rows: Manhattan LL84 rows in year y with valid electricity, plus earlier-year rows for listed buildings with none."""
    m = mn(y)
    notes = {"excluded_nonnumeric_or_negative_elec": int((m[col].isna() | (m[col] < 0)).sum())}
    m = m[m[col].notna() & (m[col] >= 0)]
    m["role"] = "other"
    listed_rows = {}
    for n, b in LIST.items():
        r = m[m.bbl == b]
        if len(r) == 0:
            # latest earlier year
            for y2 in range(y - 1, 2021, -1):
                e = mn(y2)
                e = e[(e.bbl == b) & e[col].notna() & (e[col] >= 0)]
                if len(e):
                    e = e.copy(); e["role"] = "listed"; e["from_year"] = y2
                    m = pd.concat([m, e]); listed_rows[n] = (len(e), y2); break
            else:
                listed_rows[n] = (0, None)
        else:
            m.loc[m.bbl == b, "role"] = "listed"; listed_rows[n] = (len(r), y)
    flagged = (m.dcarea > 0) & (m.role == "other")
    m.loc[flagged, "role"] = "flagged"
    notes["listed_rows"] = listed_rows
    if drop60:
        m = m[~(m.bbl == LIST["60 Hudson Street"])]
    if listonly:
        m.loc[m.role == "flagged", "role"] = "other"
    if nonflagq:
        m = m[~m.flagq]
    if parent_ok:
        m = m[m.standalone | (m.role != "other")]
    return m, notes

def shares(m, uer_total_mwh=None):
    D1 = m.elec.sum()
    U = m[m.role.isin(["listed", "flagged"])].elec.sum()
    L1 = m.it.sum(skipna=True)
    ok = m.dcarea.notna() & (m.dcarea > 0) & (m.gfa > 0)
    L2 = (np.minimum(m.dcarea[ok] / m.gfa[ok], 1) * m.elec[ok]).sum()
    L3 = (m.it * m.pue)[m.it.notna() & m.pue.notna()].sum()
    A = m.dcarea.fillna(0).sum() / m.gfa.sum()
    out = {"D1_kWh": D1, "U_kWh": U, "L1_kWh": L1, "L2_kWh": L2, "L3_kWh": L3,
           "U_over_D1_pct": 100 * U / D1, "L1_over_D1_pct": 100 * L1 / D1, "L2_over_D1_pct": 100 * L2 / D1, "L3_over_D1_pct": 100 * L3 / D1,
           "area_share_pct": 100 * A, "dc_area_ft2": m.dcarea.fillna(0).sum(), "gfa_ft2": m.gfa.sum()}
    if uer_total_mwh:
        for k in ("U", "L1", "L2", "L3"):
            out[f"{k}_over_D2_pct"] = 100 * out[f"{k}_kWh"] / 1000 / uer_total_mwh
        out["D2_MWh"] = uer_total_mwh
    return out

def boot(m, n=2000):
    fixed = m[m.role.isin(["listed", "flagged"])]
    oth = m[m.role == "other"]
    ev, iv, gv, dv = oth.elec.values, oth.it.fillna(0).values, oth.gfa.values, oth.dcarea.fillna(0).values
    Uf, Lf = fixed.elec.sum(), fixed.it.fillna(0).sum()
    out = {"U": [], "L1": [], "A": []}
    A_f_dc, A_f_g = fixed.dcarea.fillna(0).sum(), fixed.gfa.sum()
    for _ in range(n):
        i = rng.integers(0, len(oth), len(oth))
        D1 = Uf + ev[i].sum()
        out["U"].append(100 * Uf / D1)
        out["L1"].append(100 * (Lf + iv[i].sum()) / D1)
        out["A"].append(100 * (A_f_dc + dv[i].sum()) / (A_f_g + gv[i].sum()))
    return {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in out.items()}

def uer_total(y, field):
    t = uer[(uer.y == y) & (uer.data_field == field)]
    return t.v.sum(), {"cells": len(t), "cells_zero_or_blank": int((t.v.fillna(0) <= 0).sum()), "months": int(t.month.nunique()), "zips": int(t.zip_code.nunique())}

res = {}
Y = 2024
D2c, D2info = uer_total(Y, "2_nat_consumption")
D2t, _ = uer_total(Y, "3_nat_consumption")
m, notes = pick(Y)
res["primary"] = shares(m, D2c)
res["primary"]["vs_D2_total_consumption"] = {k: 100 * res["primary"][f"{k}_kWh"] / 1000 / D2t for k in ("U", "L1", "L2", "L3")}
res["primary"]["D2_total_MWh"] = D2t
res["primary"]["boot95"] = boot(m)
res["primary"]["D2_info"] = D2info
res["primary"]["notes"] = notes
res["primary"]["n_rows_D1"] = len(m)
res["primary"]["n_listed_rows"] = int((m.role == "listed").sum())
res["primary"]["n_flagged_rows"] = int((m.role == "flagged").sum())
res["primary"]["n_it_rows"] = int(m.it.notna().sum())
fl = m[m.role == "flagged"][["property_name", "address_1", "bbl", "dcarea", "gfa", "elec", "it", "largest_property_use_type", "alert_data_center_issue_with"]]
res["flagged_table"] = fl.sort_values("elec", ascending=False).to_dict("records")
lt = m[m.role == "listed"][["property_name", "address_1", "bbl", "dcarea", "gfa", "elec", "it", "largest_property_use_type"]]
res["listed_table"] = lt.sort_values("elec", ascending=False).to_dict("records")
verdict_pass_D1 = res["primary"]["U_over_D1_pct"] < THR
verdict_pass_D2 = res["primary"]["U_over_D2_pct"] < THR
res["decision"] = {"U_D1_pct": res["primary"]["U_over_D1_pct"], "U_D2_pct": res["primary"]["U_over_D2_pct"], "below_D1": bool(verdict_pass_D1), "below_D2": bool(verdict_pass_D2)}

# sensitivities
sens = {}
for y in (2023, 2022):
    mm, _ = pick(y); sens[f"year_{y}"] = shares(mm)
for name, kw in {"list_only": dict(listonly=True), "drop_60_hudson": dict(drop60=True), "exclude_estimated_or_alerts": dict(nonflagq=True),
                 "D1_no_campus_children": dict(parent_ok=True), "net_of_onsite_generation": dict(col="elec2")}.items():
    mm, _ = pick(Y, **kw)
    s_ = shares(mm, D2c)
    sens[name] = {k: s_[k] for k in ("U_over_D1_pct", "U_over_D2_pct", "L1_over_D1_pct", "area_share_pct", "D1_kWh", "U_kWh")}
res["sensitivity"] = sens

# placebos
pl = {}
b = mn(Y, "BRONX"); b = b[b.elec.notna() & (b.elec >= 0)]
bf = b[b.dcarea > 0]
pl["P1_bronx"] = {"D1_kWh": b.elec.sum(), "n_rows": len(b), "n_flagged": len(bf), "flagged_whole_building_over_D1_pct": 100 * bf.elec.sum() / b.elec.sum(),
                  "L1_over_D1_pct": 100 * b.it.sum() / b.elec.sum(), "area_share_pct": 100 * b.dcarea.fillna(0).sum() / b.gfa.sum(),
                  "flagged_rows": bf[["property_name", "address_1", "dcarea", "gfa", "elec"]].to_dict("records")}
# P2 size-matched office draws
oth = m[(m.role == "other") & (m.largest_property_use_type == "Office") & (m.gfa > 0)]
lst = m[m.role == "listed"]
draws = []
for _ in range(2000):
    tot = 0.0
    for g in lst.gfa.values:
        c = oth[(oth.gfa >= 0.75 * g) & (oth.gfa <= 1.25 * g)]
        if len(c):
            tot += c.elec.iloc[rng.integers(0, len(c))]
    draws.append(100 * tot / res["primary"]["D1_kWh"])
draws = np.array(draws)
Upct = res["primary"]["U_over_D1_pct"]
pl["P2_office_matched"] = {"n_listed_rows_matched": int(len(lst)), "listed_only_U_pct": 100 * lst.elec.sum() / res["primary"]["D1_kWh"],
    "draw_mean_pct": float(draws.mean()), "draw_p2.5": float(np.percentile(draws, 2.5)), "draw_p97.5": float(np.percentile(draws, 97.5)),
    "percentile_of_listed_only": float((draws < 100 * lst.elec.sum() / res["primary"]["D1_kWh"]).mean() * 100)}
# P3 laboratory
lab = m[m.lab > 0]
pl["P3_laboratory"] = {"n_buildings": len(lab), "area_share_pct": 100 * lab.lab.sum() / m.gfa.sum(), "whole_building_elec_share_pct": 100 * lab.elec.sum() / m.elec.sum()}
res["placebos"] = pl
(D / "datacentre_results.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: res[k] for k in ("decision", "placebos")}, indent=1, default=float))
print(json.dumps({k: v for k, v in res["primary"].items() if k != "notes"}, indent=1, default=float))
print(json.dumps(res["sensitivity"], indent=1, default=float))
print(res["primary"]["notes"])
