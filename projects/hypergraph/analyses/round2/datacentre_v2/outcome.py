import json
from pathlib import Path
from concord import claims
ROOT = Path(__file__).resolve().parents[3]
r = json.load(open(ROOT / "data/derived/round2/datacentre_v2/results.json"))
P = r["primary"]; S = r["sensitivity"]; B = r["placebo_B"]
rec = {
 "id": "further-datacentre-share-manhattan-v2",
 "verdict": "confirmed",
 "city_effect": {"label": "High figure for data-centre share of Manhattan LL84 grid electricity, CY2024, minus 4.4 percent", "estimate": round(P["S_hi_over_D1_pct"] - 4.4, 2),
                 "lo": round(P["boot95_D1"]["S_hi"][0] - 4.4, 2), "hi": round(P["boot95_D1"]["S_hi"][1] - 4.4, 2), "scale": "percentage points", "null": 0, "n": P["n_rows_D1"],
                 "note": "Bootstrap over the buildings outside the numerator; it excludes reporting error, tenant metering and the choice of PUE and baseline. Low figure 1.01 percent (0.96 to 1.06)."},
 "graph_effect": None,
 "sources": [
  {"kind": "nyc-open-data", "dataset": "5zyy-y8am", "name": "NYC Building Energy and Water Data Disclosure for Local Law 84 2023 to Present (Data for Calendar Year 2022-Present)", "url": "https://data.cityofnewyork.us/d/5zyy-y8am",
   "rows_updated_at": "2025-11-25T19:02:35Z", "note": "cached query of the first claim, data/derived/further/datacentre_sources.json; no new LL84 query", "data_access": "open"},
  {"kind": "nyc-open-data", "dataset": "g2x3-izm4", "name": "Utility Energy Registry Monthly ZIP Code Energy Use: Beginning 2021", "url": "https://data.ny.gov/d/g2x3-izm4",
   "note": "Manhattan non-residential (cached) and all New York City ZIP codes total consumption (new, data/derived/round2/datacentre_v2/sources_uer_nyc.json); 2023 has only six months and is not used as a denominator", "data_access": "open", "domain": "https://data.ny.gov"},
  {"kind": "other", "name": "NYISO integrated real-time load, Zone J (N.Y.C.), 2024 daily energy", "note": "cached file data/derived/further/zonej_daily.csv", "data_access": "open"},
  {"kind": "other", "name": "LBNL summary of the 2024 United States Data Center Energy Usage Report", "url": "https://energyanalysis.lbl.gov/news/berkeley-lab-report-evaluates-increase-electricity-demand-data-centers", "quote": "Data centers consumed about 4.4% of total U.S. electricity in 2023", "fetched": "2026-11-12", "data_access": "partly_open"},
  {"kind": "other", "name": "EPRI, Powering Intelligence (2024 white paper)", "url": "https://restservice.epri.com/publicdownload/000000003002028905/0/Product", "quote": "a quarter of Virginia's electric load in 2023", "fetched": "2026-11-12", "data_access": "partly_open"},
 ],
 "prediction_scored": (f"hit on all four conditions, one at the edge. (a) S_high {P['S_hi_over_D1_pct']:.2f} percent of D1 and {P['S_hi_over_D2_pct']:.2f} of D2, both below 4.4. (b) S_low {P['S_lo_over_D1_pct']:.2f} percent of D1, inside 1.0 to 1.3 by 0.01. "
                       f"(c) S_high {P['S_hi_over_D1_pct']:.2f} inside 1.8 to 3.5. (d) listed-building excess {B['listed_B_pct_D1']:.2f} percent of D1 against a placebo 97.5th percentile of {B['p97.5']:.2f}."),
 "settle": "Metered data-centre electricity for the carrier hotels and colocation buildings: Con Edison service-class or account data, or tenant-metered Portfolio Manager IT meters. Landlord-reported grid electricity omits tenant meters, so the figures here are allocations and not measurements.",
 "research_needed": [{"question": "How much carrier-hotel electricity is tenant-metered and absent from LL84?", "data": "Con Edison account-level data (not open); Local Law 97 reports by space type", "design": "Compare landlord grid electricity with Con Edison delivery to the lot", "priority": "high"}],
 "figures": ["figures/round2/datacentre_share_v2.png"],
 "notes": (f"Primary 2024. D1 {P['D1_kWh']/1e9:.2f} TWh (matches the first run), D2 {r['denominators']['D2_MWh']/1e6:.2f} TWh, D3 {r['denominators']['D3_MWh']/1e6:.2f} TWh (Zone J {r['denominators']['zoneJ_MWh']/1e6:.2f} TWh times Manhattan's {100*r['denominators']['mn_share_of_nyc']:.1f} percent of Con Edison New York City deliveries, 208 ZIP codes). "
           f"Allocated electricity: low {P['S_lo_kWh']/1e6:.0f} GWh, high {P['S_hi_kWh']/1e6:.0f} GWh. Shares: D1 {P['S_lo_over_D1_pct']:.2f} to {P['S_hi_over_D1_pct']:.2f} percent (bootstrap 0.96 to 1.06, 2.15 to 2.38); D2 {P['S_lo_over_D2_pct']:.2f} to {P['S_hi_over_D2_pct']:.2f}; D3 {P['S_lo_over_D3_pct']:.2f} to {P['S_hi_over_D3_pct']:.2f}. "
           f"Median office intensity {r['median_office_kWh_per_ft2']:.1f} kWh per square foot (538 offices); this is low, probably because landlord figures omit tenant meters, which raises B. "
           "The cap binds: the 56 Hudson Street property (Western Union Building) reports IT energy equal to 90 percent of its grid electricity, so IT x 1.4 exceeds the building total, and it supplies half of the low figure. 19 buildings report positive IT energy (the first run's 26 included zero values), 3 of them listed. The BBL for 60 Hudson Street again joins to 56 Hudson Street. "
           f"B alone is {P['B_over_D1_pct']:.2f} percent of D1; 111 Eighth Avenue (53 kWh per square foot) contributes 107 GWh of it. "
           f"Sensitivity (D1 high figure): uncapped {S['uncapped']['S_hi_over_D1_pct']:.2f}; 2023 {S['year_2023']['S_lo_over_D1_pct']:.2f} to {S['year_2023']['S_hi_over_D1_pct']:.2f}; adding area-proportional electricity for 150 other buildings with data-centre floor area gives {S['flagged_area_proportional_added_to_S_hi']['S_hi_over_D1_pct']:.2f}. "
           f"Dropping estimated or alert rows leaves a 6.6 TWh D1 and gives {S['drop_flagged_rows']['S_lo_over_D1_pct']:.1f} to {S['drop_flagged_rows']['S_hi_over_D1_pct']:.1f} percent, a different and smaller population. "
           f"Reverse bound: unreported data-centre load would have to be {r['reverse_bound_R_D1']:.1f} times the allocated high figure for the D1 share to reach 4.4 percent. Bronx placebo: no IT-reporting building. "
           "Condition (a) was judged before the test to be almost incapable of failing (registered probability 0.03); the verdict rests on (b), (c) and (d). The placebo for (d) uses a median baseline, so its draws sit near zero by construction."),
}
print(claims.outcome(rec))
