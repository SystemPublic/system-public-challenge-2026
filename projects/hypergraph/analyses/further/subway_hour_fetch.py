"""Fetch for further-subway-crime-per-ride-by-hour (run after registration). Server-side aggregates only.
    PYTHONPATH=. ~/.venvs/nyc-concordance/bin/python -m analyses.further.subway_hour_fetch
"""
import json
from pathlib import Path
from concord import socrata as S

OUT = Path(__file__).resolve().parents[2] / "data" / "derived" / "further_subway"
OUT.mkdir(parents=True, exist_ok=True)
KY = "(101,104,105,106,107,109,110)"
NYC = "https://data.cityofnewyork.us"
NYS = "https://data.ny.gov"
sources = []


def run(domain, ds, **q):
    S.DOMAIN = domain
    rows, src = S.query_all(ds, **q) if q.get("order") else S.query(ds, **q)
    src["domain"] = domain
    sources.append(src)
    return rows


COMPL = [("qgea-i56i", "2019-01-01T00:00:00", "2025-12-31T23:59:59"),
         ("5uac-w243", "2026-01-01T00:00:00", "2026-09-30T23:59:59")]
SEL = ("date_extract_y(cmplnt_fr_dt) as y, date_extract_m(cmplnt_fr_dt) as m, "
       "substring(cmplnt_fr_tm,1,2) as hh, "
       "case(cmplnt_fr_tm in ('00:00:00','12:00:00'),1,true,0) as rnd")
out = {}
for ds, lo, hi in COMPL:
    w = f"cmplnt_fr_dt between '{lo}' and '{hi}' and law_cat_cd='FELONY' and ky_cd in {KY}"
    out[f"{ds}_subway"] = run(NYC, ds, select=SEL + ", ky_cd, prem_typ_desc, count(*) as n",
        where=w + " and prem_typ_desc in ('TRANSIT - NYC SUBWAY','TRANSIT FACILITY (OTHER)')",
        group="y,m,hh,rnd,ky_cd,prem_typ_desc", limit=50000)
    out[f"{ds}_district"] = run(NYC, ds, select=SEL + ", ky_cd, count(*) as n",
        where=w + " and transit_district is not null", group="y,m,hh,rnd,ky_cd", limit=50000)
    out[f"{ds}_nonsubway"] = run(NYC, ds, select=SEL + ", count(*) as n",
        where=w + " and (prem_typ_desc is null or prem_typ_desc not in ('TRANSIT - NYC SUBWAY','TRANSIT FACILITY (OTHER)','TUNNEL','BRIDGE'))",
        group="y,m,hh,rnd", limit=50000)
    out[f"{ds}_all"] = run(NYC, ds, select="count(*) as n", where=w)
    print(ds, "done", flush=True)

PER = [("t69i-h2me", "2019-01-01T00:00:00", "2019-12-31T23:59:59")] + \
      [("wujg-7c2s", f"{y}-{m1:02d}-01T00:00:00", ("%d-06-30T23:59:59" % y if m2 == 6 else "%d-12-31T23:59:59" % y)) for y in range(2020, 2025) for m1, m2 in ((1, 6), (7, 12))] + \
      [("5wq4-mkjj", "2025-01-01T00:00:00", "2025-12-31T23:59:59"), ("5wq4-mkjj", "2026-01-01T00:00:00", "2026-11-05T23:59:59")]
for ds, lo, hi in PER:
    out.setdefault(f"rid_{ds}", [])
    out[f"rid_{ds}"] += run(NYS, ds, select="date_extract_y(transit_timestamp) as y, date_extract_m(transit_timestamp) as m, date_extract_hh(transit_timestamp) as hh, sum(ridership) as n",
        where=f"transit_mode='subway' and transit_timestamp between '{lo}' and '{hi}'", group="y,m,hh", limit=50000)
    print(ds, "done", flush=True)

out["yeek"] = run(NYS, "yeek-jhmu", select="month,agency,police_force,felony_type,felony_count,crimes_per_million_riders", order="month,agency,police_force,felony_type")
(OUT / "raw.json").write_text(json.dumps(out))
(OUT / "sources.json").write_text(json.dumps(sources, indent=1))
print("ok", {k: len(v) for k, v in out.items()})
