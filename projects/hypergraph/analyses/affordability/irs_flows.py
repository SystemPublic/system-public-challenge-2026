"""IRS Statistics of Income county-to-county outflows for the five New York City counties.
Files: https://www.irs.gov/pub/irs-soi/countyoutflow{1112,1516,1920,2122}.csv (kept outside Dropbox).
Writes data/derived/affordability/irs_outflows.json: for each period and borough, returns and people who left,
their mean adjusted gross income (AGI) per return against that of non-movers, and destinations grouped by region."""
import json, os
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
RAW = Path(os.path.expanduser("~/opt/nyc-concordance/affordability/irs"))
NYC = {5: "Bronx", 47: "Brooklyn", 61: "Manhattan", 81: "Queens", 85: "Staten Island"}
INNER = {(36, 59), (36, 103), (36, 119), (36, 87), (34, 3), (34, 13), (34, 17), (34, 23), (34, 39), (34, 31), (34, 25), (34, 27), (34, 35), (9, 1)}
def region(s, c):
    if s == 36 and c in NYC: return "other NYC borough"
    if (s, c) in INNER: return "nearby suburbs (Long Island, Westchester, Rockland, north-east New Jersey, Fairfield)"
    if s in (36, 34, 9, 42): return "rest of NY, NJ, CT, PA"
    if s == 12: return "Florida"
    if s == 57: return "abroad"
    return "rest of United States"
out = {}
for per in ["1112", "1516", "1920", "2122"]:
    d = pd.read_csv(RAW / f"countyoutflow{per}.csv", encoding="latin-1")
    d = d[(d.y1_statefips == 36) & (d.y1_countyfips.isin(NYC))]
    res = {}
    for c, name in NYC.items():
        x = d[d.y1_countyfips == c]
        tot = x[(x.y2_statefips == 96) & (x.y2_countyfips == 0)].iloc[0]
        stay = x[(x.y2_statefips == 36) & (x.y2_countyfips == c)].iloc[0]
        det = x[(x.y2_statefips < 58) & ~((x.y2_statefips == 36) & (x.y2_countyfips == c)) & (x.n1 > 0)].copy()
        det = det[~det.y2_countyname.str.contains("Other flows|Total Migration|Non-migrants", case=False)]
        det["region"] = [region(s, k) for s, k in zip(det.y2_statefips, det.y2_countyfips)]
        g = det.groupby("region").agg(returns=("n1", "sum"), people=("n2", "sum"), agi=("agi", "sum"))
        g["agi_per_return"] = g.agi * 1000 / g.returns
        top = det.sort_values("n2", ascending=False).head(8)
        res[name] = {"movers_returns": int(tot.n1), "movers_people": int(tot.n2), "movers_agi_per_return": float(tot.agi * 1000 / tot.n1),
                     "stayers_returns": int(stay.n1), "stayers_agi_per_return": float(stay.agi * 1000 / stay.n1),
                     "share_leaving": float(tot.n1 / (tot.n1 + stay.n1)),
                     "identified_by_region": {r: {"people": int(v.people), "agi_per_return": float(v.agi_per_return)} for r, v in g.iterrows()},
                     "top_destinations": [{"county": f"{r.y2_countyname}, {r.y2_state}", "people": int(r.n2), "agi_per_return": float(r.agi * 1000 / r.n1)} for r in top.itertuples()]}
    out[per] = res
(ROOT / "data/derived/affordability/irs_outflows.json").write_text(json.dumps(out, indent=1))
for per in ("1112", "2122"):
    for b, v in out[per].items():
        print(per, b, v["movers_people"], round(v["share_leaving"], 3), round(v["movers_agi_per_return"]), round(v["stayers_agi_per_return"]),
              {k[:12]: (x["people"], round(x["agi_per_return"])) for k, x in v["identified_by_region"].items()})
        print("   ", [(t["county"], t["people"], round(t["agi_per_return"])) for t in v["top_destinations"][:5]])
