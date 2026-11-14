"""Write the outcome of levers-vacant-lot-trial-match from data/derived/levers/lot_test_results.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

D = ROOT / "data" / "derived" / "levers"
r = json.loads((D / "lot_test_results.json").read_text())
src = json.loads((D / "lots_sources.json").read_text())["sources"]
cm = json.loads((D / "city_metrics.json").read_text())["sources"]
poly = json.loads((D / "lot_polygons_source.json").read_text())
p = r["prevented_per_year"]

rec = {
    "id": "levers-vacant-lot-trial-match",
    "verdict": "confirmed",
    "city_effect": {"label": "Share of land use 11 lots in the top-decile shooting tracts that resemble the Philadelphia trial lots",
                    "estimate": r["trial_like_share"], "lo": None, "hi": None, "scale": "share of lots (a count, no sampling interval: every lot was classified)",
                    "null": None, "n": r["n_lu11_in_high_shooting_tracts"]},
    "graph_effect": {"label": "Moyer et al. 2019: greening, change in shootings near the lot", "estimate": -6.8, "lo": -10.6, "hi": -2.7,
                     "scale": "% change", "null": 0},
    "sources": [src[k] for k in src] + [cm["shootings"],
                {"kind": "other", "name": "MapPLUTO lot polygons, DCP ArcGIS feature service", "url": poly["url"], "version": poly["versions"], "fetched": poly["fetched"]},
                {"kind": "other", "name": "USDA NAIP 2022, New York flight, via Microsoft Planetary Computer STAC (collection naip)", "url": "https://planetarycomputer.microsoft.com/api/stac/v1/collections/naip"},
                {"kind": "literature", "name": "Moyer et al. 2019 AJPH, PMID 30496003"}],
    "prediction_scored": (f"hit. The trial-like share was {r['trial_like_share']:.3f} (registered 0.18 to 0.45, central 0.30) and the number "
                          f"{r['trial_like_n']:,} (registered 400 to 1,500, central 800). Lots in high-shooting tracts: {r['n_lu11_in_high_shooting_tracts']:,} "
                          f"(registered 2,000 to 3,500). Shootings within 300 m: {r['shootings_within_300m_trial_like_per_year']} a year "
                          f"(registered 250 to 450). Prevented by greening: {p['greening']['estimate']} ({p['greening']['lo']} to {p['greening']['hi']}) "
                          f"a year (registered about 20, 8 to 40). The share is near the top of its range."),
    "settle": ("Whether the trial-like lots are blighted as the trial required cannot be seen in NDVI. A street-level survey of a random sample "
               "of the 1,116 lots (trash, overgrowth, fencing, use as a side yard) would settle how many qualify; a randomised greening programme "
               "in New York would settle whether the Philadelphia effect transfers."),
    "research_needed": [
        {"question": "How many of New York's trial-like lots are blighted (trash, overgrowth) rather than maintained side yards or private gardens?",
         "data": "street-level survey or Street View of a stratified sample", "design": "random sample of the 1,116 lots, two coders", "priority": "high"},
        {"question": "Does vacant-lot greening reduce shootings in New York, where lots are smaller, denser and more often privately held for development?",
         "data": "NYPD shootings, the lot list from this claim", "design": "cluster randomised trial with the city's or a charity's lot programme", "priority": "high"},
        {"question": "Does the effect diminish when many treated lots lie within 300 m of the same shootings?",
         "data": "Philadelphia trial data by cluster density", "design": "re-analysis", "priority": "medium"},
    ],
    "figures": ["figures/levers/map_greening.png", "figures/levers/lot_contact_sheet.png"],
    "notes": (
        f"All {r['n_lu11_in_high_shooting_tracts']:,} land use 11 lots in the 235 tracts with 10 or more shootings in 2019-2024 were classified by records; "
        f"by type: {r['by_type_high_shooting']}. No GreenThumb garden and no buyout parcel fell in these tracts (gardens are mostly land use 9). "
        f"After the size limit of 510 m2, {sum(v for k, v in r['small_by_type_high_shooting'].items() if k in ('private_idle', 'city_interim')):,} private-idle or city-interim lots remained, "
        "fewer than the 2,500 at which the plan called for sampling, so NAIP was read for every one (and for the small stalled and active lots, for comparison). "
        f"Of the small idle lots, NAIP 2022 classed {r['naip_class_of_small_idle']}. Trial-like lots: {r['trial_like_n']:,} "
        f"(owners: {r['trial_like_by_owner']}; boroughs: {r['trial_like_by_borough']}), {r['trial_like_area_m2_total']:,} m2 in all. "
        f"Without the imagery filter the count is {r['trial_like_without_imagery_n']:,}; adding stalled lots gives {r['trial_like_with_stalled_n']:,}. "
        f"{r['shootings_within_300m_trial_like_per_year']} shootings a year (2023-2025) fell within 300 m of a trial-like lot, of {r['shootings_citywide_per_year_2023_2025']} citywide. "
        f"At the trial's effects, greening all of them would prevent {p['greening']['estimate']} ({p['greening']['lo']} to {p['greening']['hi']}) shootings a year, "
        f"cleanup {p['cleanup']['estimate']} ({p['cleanup']['lo']} to {p['cleanup']['hi']}); the intervals are the trial's only and leave out the doubt about transfer. "
        f"At the trial's costs ($5 per m2, $0.50 per m2 a year) greening would cost about ${r['cost_initial_usd']:,} and ${r['cost_maintenance_usd_per_year']:,} a year. "
        "Two problems were found after the data were read. The shooting dataset (5ucz-vwe8) as fetched has its latitude and longitude columns swapped; the analysis swaps them back. "
        "BIS permits for new buildings end in May 2020, so recent development activity rests on DOB NOW foundation, earthwork and demolition permits and on new-building filings. "
        "An exploratory visual check of 40 random lot images found that 4 of the 18 lots the rule calls trial-like show a building roof or a maintained ball field, "
        "so the count may be about a fifth too high; the share would still lie in the registered range."
    ),
}
print(claims.outcome(rec))
