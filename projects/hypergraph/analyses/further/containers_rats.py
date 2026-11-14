"""Analysis for further-containers-rats-cd9 and further-repro-dsny-rat-sightings (registered plan)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from concord import socrata as S
OUTD = ROOT / "data" / "derived" / "further"; OUTD.mkdir(parents=True, exist_ok=True)
srcs = []
def q(ds, **k):
    r, s = S.query(ds, **k); srcs.append(s); return pd.DataFrame(r)

# 311 monthly by board, Manhattan, Rodent descriptors and two placebo types
a = q("erm2-nwe9", select="date_trunc_ym(created_date) as m, community_board as cb, complaint_type as ct, descriptor as d, count(*) as n",
      where="created_date >= '2022-01-01T00:00:00' and borough='MANHATTAN' and (complaint_type='Rodent' or complaint_type='Noise - Residential')",
      group="m, cb, ct, d", order="m, cb, ct, d")
a["n"] = a.n.astype(int); a["m"] = pd.to_datetime(a.m).dt.to_period("M"); a["cd"] = a.cb.str[:2]
# citywide monthly Rodent by descriptor (reproduction)
c = q("erm2-nwe9", select="date_trunc_ym(created_date) as m, borough as b, descriptor as d, count(*) as n",
      where="created_date >= '2022-12-01T00:00:00' and complaint_type='Rodent'", group="m, b, d", order="m, b, d")
c["n"] = c.n.astype(int); c["m"] = pd.to_datetime(c.m).dt.to_period("M")
# DOHMH
h = q("p937-wjvj", select="date_trunc_ym(inspection_date) as m, community_board as cb, "
      "sum(case(starts_with(result,'Failed for Rat Activity'),1,true,0)) as act, count(*) as n",
      where="borough='Manhattan' and inspection_type='Initial' and inspection_date >= '2022-01-01T00:00:00'", group="m, cb", order="m, cb")
for k in ("act", "n"): h[k] = h[k].astype(int)
h["m"] = pd.to_datetime(h.m).dt.to_period("M")
a.to_csv(OUTD/"cd_monthly_311.csv", index=False); c.to_csv(OUTD/"citywide_rodent_monthly.csv", index=False); h.to_csv(OUTD/"dohmh_initial_monthly.csv", index=False)

P = pd.Period
def win(s, e): return pd.period_range(s, e, freq="M")
TR, CMP = "09", ["07", "10", "11", "12"]
rng = np.random.default_rng(20261112)

def series(df, cdcol, val, cds, months, col="n"):
    d = df[df[cdcol].isin(cds) & df.m.isin(months)].groupby("m")[col].sum()
    return d.reindex(months, fill_value=0).values.astype(float)

def did(tp, tq, cp, cq, B=4000):
    """tp,tq: treated post, pre monthly arrays (aligned pairs); cp,cq comparison. Ratio-of-ratios + month-pair bootstrap."""
    f = lambda i: (tp[i].sum()/tq[i].sum())/(cp[i].sum()/cq[i].sum())
    n = len(tp); est = f(np.arange(n))
    bs = np.array([f(rng.integers(0, n, n)) for _ in range(B)])
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

def did_share(num_t, den_t, num_c, den_c, B=4000):
    """arrays: [post, pre] monthly numerators/denominators for treated and comparison; odds-ratio of ratios."""
    def f(i):
        def odds(nu, de): p = nu[i].sum()/de[i].sum(); return p/(1-p)
        return (odds(num_t[0], den_t[0])/odds(num_t[1], den_t[1]))/(odds(num_c[0], den_c[0])/odds(num_c[1], den_c[1]))
    n = len(num_t[0]); est = f(np.arange(n))
    bs = np.array([f(rng.integers(0, n, n)) for _ in range(B)])
    return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

res = {}
def run311(df, post, pre, cmp=CMP, desc=("Rat Sighting",), ct="Rodent"):
    d = df[(df.ct == ct) & (df.d.isin(desc))]
    g = lambda cds, mm: series(d, "cd", None, cds, mm)
    tp, tq, cp, cq = g([TR], post), g([TR], pre), g(cmp, post), g(cmp, pre)
    e = did(tp, tq, cp, cq)
    return dict(R=e[0], lo=e[1], hi=e[2], t_post=tp.sum(), t_pre=tq.sum(), c_post=cp.sum(), c_pre=cq.sum())
W = dict(post=win("2025-06", "2026-05"), pre=win("2024-06", "2025-05"))
res["primary"] = run311(a, **W)
res["placebo_year"] = run311(a, win("2023-06", "2024-05"), win("2022-06", "2023-05"))
last = a.m.max(); res["last_month_in_data"] = str(last)
res["w6"] = run311(a, win("2025-06", "2025-11"), win("2024-06", "2024-11"))
lastcomplete = P("2026-10", "M")
res["w17"] = run311(a, win("2025-06", "2026-10"), win("2024-06", "2025-10"))
for k in CMP: res["only_" + k] = run311(a, **W, cmp=[k])
for k in CMP: res["loo_" + k] = run311(a, **W, cmp=[x for x in CMP if x != k])
res["all_manhattan"] = run311(a, **W, cmp=["01","02","03","04","05","06","07","08","10","11","12"])
res["all_rodent_desc"] = run311(a, **W, desc=tuple(a[a.ct=="Rodent"].d.unique()))
res["placebo_noise"] = run311(a, **W, ct="Noise - Residential", desc=tuple(a[a.ct=="Noise - Residential"].d.unique()))
res["placebo_noise_prior_year"] = run311(a, win("2023-06","2024-05"), win("2022-06","2023-05"), ct="Noise - Residential", desc=tuple(a[a.ct=="Noise - Residential"].d.unique()))
# event study by quarter: CD9 / comparison ratio, indexed to Jun24-May25 mean
d = a[(a.ct=="Rodent")&(a.d=="Rat Sighting")]
t = d[d.cd==TR].groupby("m").n.sum(); cc = d[d.cd.isin(CMP)].groupby("m").n.sum()
ev = pd.DataFrame({"cd9": t, "cmp": cc}).fillna(0); ev["ratio"] = ev.cd9/ev.cmp
ev.to_csv(OUTD/"event_series.csv")
# DOHMH
hh = h.copy(); hh["cd"] = hh.cb.astype(str).str.zfill(2)
def dohmh(post, pre, cmp=CMP):
    def arr(cds, mm, col): return series(hh, "cd", None, cds, mm, col)
    nt = [arr([TR], post, "act"), arr([TR], pre, "act")]; dt = [arr([TR], post, "n"), arr([TR], pre, "n")]
    nc = [arr(cmp, post, "act"), arr(cmp, pre, "act")]; dc = [arr(cmp, post, "n"), arr(cmp, pre, "n")]
    e = did_share(nt, dt, nc, dc)
    return dict(OR=e[0], lo=e[1], hi=e[2], t_share_post=nt[0].sum()/dt[0].sum(), t_share_pre=nt[1].sum()/dt[1].sum(),
                c_share_post=nc[0].sum()/dc[0].sum(), c_share_pre=nc[1].sum()/dc[1].sum(),
                t_n_post=dt[0].sum(), t_n_pre=dt[1].sum(), c_n_post=dc[0].sum(), c_n_pre=dc[1].sum())
res["dohmh_primary"] = dohmh(**W)
res["dohmh_placebo_year"] = dohmh(win("2023-06","2024-05"), win("2022-06","2023-05"))
res["dohmh_last_month"] = str(hh.m.max())
# reproduction
def cwin(mask, s, e): 
    return int(c[mask & c.m.isin(win(s, e))].n.sum())
five = c.b.isin(["MANHATTAN","BROOKLYN","BRONX","QUEENS","STATEN ISLAND"])
rs = {"R1": c.d=="Rat Sighting", "R2": c.d.isin(["Rat Sighting","Signs of Rodents"]), "R3": c.d.notna(), "R4": (c.d=="Rat Sighting")&five}
rep = {}
for k, m in rs.items():
    x, y = cwin(m, "2023-12", "2024-11"), cwin(m, "2024-12", "2025-11")
    rep[k] = dict(y1=x, y2=y, decline_pct=100*(y/x-1), rel_err1=x/25230-1, rel_err2=y/20025-1)
res["repro"] = rep
m1 = c[rs["R1"]].groupby("m").n.sum()
res["repro_monthly_R1"] = {str(p): [int(m1.get(p-12,0)), int(m1.get(p,0))] for p in win("2024-12","2025-11")}
def ytd(end): 
    a_, b_ = m1[win("2025-01", end)].sum(), m1[win("2024-01", str(P(end,"M")-12))].sum(); return 100*(a_/b_-1)
res["repro_ytd"] = {e: ytd(e) for e in ("2025-06","2025-07","2025-08")}
res["sources"] = srcs
(OUTD/"results.json").write_text(json.dumps(res, indent=1, default=float))
for k, v in res.items():
    if k not in ("sources","repro_monthly_R1"): print(k, json.dumps(v, default=lambda x: round(float(x),4)))
print(res["repro_monthly_R1"])
