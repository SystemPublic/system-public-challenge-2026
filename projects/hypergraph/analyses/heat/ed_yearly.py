"""heat-ed-syndromic, registered secondary: EHDP yearly citywide heat ED visits (indicator 2075, SPARCS)
and heat deaths (2074, vital statistics) against Central Park days with TMAX >= 32.2 C (90 F), May-September.
Outputs data/derived/heat/ehdp_yearly.csv and ehdp_yearly_results.json.
"""
from __future__ import annotations

import json

import pandas as pd
import requests
from scipy.stats import spearmanr

from analyses.heat.common import DER
from analyses.heat.ed_syndromic import SHA, source
from concord import noaa

E = DER / "ehdp"


def indicator(i: int) -> pd.DataFrame:
    f = E / f"indicator_{i}.json"
    if not f.exists():
        E.mkdir(parents=True, exist_ok=True)
        f.write_bytes(requests.get(f"https://raw.githubusercontent.com/nychealth/EHDP-data/{SHA}/indicators/data/{i}.json", timeout=60).content)
    return pd.DataFrame(json.loads(f.read_text()))


def periods() -> dict:
    f = E / "TimePeriods.json"
    if not f.exists():
        f.write_bytes(requests.get(f"https://raw.githubusercontent.com/nychealth/EHDP-data/{SHA}/indicators/metadata/TimePeriods.json", timeout=60).content)
    return {p["TimePeriodID"]: p for p in json.loads(f.read_text())}


def main():
    tp = periods()
    w, src_w = noaa.daily("central_park")
    ws = w[w.index.month.isin([5, 6, 7, 8, 9])]
    hot = (ws["TMAX"] >= 32.2).groupby(ws.index.year).sum().rename("days_90f")
    hot95 = (ws["TMAX"] >= 35.0).groupby(ws.index.year).sum().rename("days_95f")
    rows = []
    for ind, meas, name in [(2074, 534, "heat_deaths"), (2075, 535, "heat_ed_visits")]:
        x = indicator(ind)
        x = x[(x["MeasureID"] == meas) & (x["GeoType"] == "Citywide")]
        for _, r in x.iterrows():
            p = tp[r["TimePeriodID"]]
            if p["TimeType"].lower() not in ("year", "summer", "annual", "calendar year"):
                continue
            try:
                yr = int(str(p["TimePeriod"])[:4])
            except ValueError:
                continue
            rows.append({"year": yr, "measure": name, "value": float(r["Value"]), "period": p["TimePeriod"], "timetype": p["TimeType"]})
    t = pd.DataFrame(rows).pivot_table(index="year", columns="measure", values="value").join(hot).join(hot95)
    t.to_csv(DER / "ehdp_yearly.csv")
    out = {}
    for m in ("heat_deaths", "heat_ed_visits"):
        s = t[[m, "days_90f"]].dropna()
        r = spearmanr(s[m], s["days_90f"])
        r2 = spearmanr(t[[m, "days_95f"]].dropna()[m], t[[m, "days_95f"]].dropna()["days_95f"])
        out[m] = {"years": [int(s.index.min()), int(s.index.max())], "n": int(len(s)), "rho_days_90f": float(r.statistic),
                  "p": float(r.pvalue), "rho_days_95f": float(r2.statistic), "p_95f": float(r2.pvalue)}
    out["sources"] = [source("indicators/data/2074.json"), source("indicators/data/2075.json"), src_w]
    (DER / "ehdp_yearly_results.json").write_text(json.dumps(out, indent=1))
    print(t.to_string())
    print(json.dumps({k: v for k, v in out.items() if k != "sources"}, indent=1))


if __name__ == "__main__":
    main()
