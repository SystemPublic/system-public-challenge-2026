import json
from pathlib import Path
from concord import claims
ROOT = Path(__file__).resolve().parents[2]
r = json.load(open(ROOT / "data/derived/further/datacentre_results.json"))
srcs = json.load(open(ROOT / "data/derived/further/datacentre_sources.json"))
p = r["primary"]
srcs = srcs + [
 {"kind": "other", "name": "LBNL summary of the 2024 United States Data Center Energy Usage Report", "url": "https://energyanalysis.lbl.gov/news/berkeley-lab-report-evaluates-increase-electricity-demand-data-centers", "vintage": "page dated 2025-01-17, adapting the DOE release of 2024-12-20", "quote": "Data centers consumed about 4.4% of total U.S. electricity in 2023", "data_access": "partly_open", "fetched": "2026-11-12"}]
for s in srcs[:2]:
    s["data_access"] = "open"
srcs[1]["domain"] = "https://data.ny.gov"
eff = {"label": "Upper-bound data-centre share of Manhattan LL84 grid electricity, CY2024, minus 4.4 percent", "estimate": round(p["U_over_D1_pct"] - 4.4, 2),
       "lo": round(p["boot95"]["U"][0] - 4.4, 2), "hi": round(p["boot95"]["U"][1] - 4.4, 2), "scale": "percentage points", "null": 0, "n": p["n_rows_D1"],
       "note": "Interval is a bootstrap over the non-listed buildings; it does not include reporting error or the choice of building set. Against D2 the share is %.1f percent." % p["U_over_D2_pct"]}
rec = {
 "id": "further-datacentre-share-manhattan",
 "verdict": "contested",
 "city_effect": eff,
 "graph_effect": None,
 "sources": srcs,
 "prediction_scored": "miss on the deciding measure: registered U range 1.0 to 5.0 percent of D1, observed 16.2 percent (15.5 to 16.9), refute_if met against D1 and D2. Hit on the two lower bounds: IT energy 0.83 percent of D1 (registered 0.05 to 1.0) and area share 0.39 percent (registered below 0.5). The fixed list alone gives 2.2 percent, inside the registered range, but that is a sensitivity check and decides nothing.",
 "settle": "Metered data-centre electricity for the listed buildings: Con Edison account or service-class data, tenant-metered Portfolio Manager IT meters, or Local Law 97 reports by space type. The registered whole-building bound for buildings with any data-centre area cannot be below 4.4 percent and so cannot settle the question.",
 "research_needed": [
  {"question": "What share of Manhattan electricity delivered by Con Edison goes to data-centre and carrier-hotel accounts?", "data": "Con Edison account-level or service-class data (not open); tenant-metered IT meters", "design": "Sum metered load of identified colocation accounts over D2", "priority": "high"},
  {"question": "Is the flagged-building rule a usable bound?", "data": "LL84 data-centre floor area against space-type electricity from Portfolio Manager", "design": "Replace whole-building electricity by area times a data-centre intensity from buildings reporting IT meters (26 in 2024)", "priority": "medium"},
  {"question": "Why do 2024 rows carry no PUE (2 values in the whole file)?", "data": "LL84 data-centre fields, DOB benchmarking help documents", "design": "Check whether the field is dropped from the public release", "priority": "low"},
 ],
 "figures": ["figures/further/datacentre_share_manhattan.png"],
 "notes": "Upper bound U (whole buildings: 10 listed plus 165 flagged) is 2.76 TWh of D1 17.06 TWh and 17.2 percent of D2 16.03 TWh (UER non-residential, 12 months, 68 ZIP codes, 197 of 809 cells zero or blank); against UER total consumption 18.33 TWh it is 15.0 percent. List alone: 2.23 percent of D1, 2.37 of D2. Lower bounds: IT energy 0.83 percent of D1 (0.79 to 0.86), 0.88 of D2; area-proportional 1.51 and 1.61; area share 0.39 percent (0.38 to 0.41); PUE-scaled not computable for 2024. Sensitivity U/D1: 2023 15.8, 2022 17.0, drop 60 Hudson lot 15.7, drop estimated or alert rows 20.6 (D1 6.60 TWh), no campus child rows 20.1, net of on-site generation 16.2. Placebos: Bronx whole-building share of 12 flagged buildings 1.67 percent, IT energy 0.00, area share 0.23; size-matched office draws 0.62 percent (0.44 to 0.96) against 2.23 for the list; laboratory buildings 0.59 percent of area and 4.57 percent of electricity, which shows the whole-building rule can exceed 4.4 percent for a non-data-centre use. The BBL join for 60 Hudson Street returned the 56 Hudson Street property; the Western Union Building row was last reported for 2023 and was not used. The verdict follows the registered refutation rule (PRECEDENCE rule 1) and is a property of the registered flagged-building component. Coverage limits: LL84 large buildings only; tenant sub-metering; 1,290 rows without usable electricity; D1 includes residential, D2 does not.",
}
print(claims.outcome(rec))
