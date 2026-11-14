"""Write the outcome for mob-crz-traffic from data/derived/mobility/crz_traffic_results.json."""
import json

from concord import claims
from analyses.mobility.common import DER

R = json.loads((DER / "crz_traffic_results.json").read_text())
r = R["results"]
sp, tr, pl = r["speed_CBD_vs_Greater NYC"], r["trips_CBD_vs_outside"], r["trips_CBD_vs_outside_placebo2024"]

rec = {
    "id": "mob-crz-traffic",
    "verdict": "confirmed",
    "city_effect": {"label": "CBD vs rest-of-city taxi/FHV speed, 2025 vs 2023-24 (DiD)",
                    "estimate": round(sp["pct"], 2), "lo": round(sp["lo_pct"], 2), "hi": round(sp["hi_pct"], 2),
                    "scale": "percent change in speed", "null": 0, "n": sp["n"]},
    "graph_effect": {"label": "No road-pricing findings in the System graph; literature: Stockholm and London traffic across the cordon -18% to -21%",
                     "estimate": None, "lo": None, "hi": None, "scale": "percent change in traffic", "null": 0},
    "sources": R["sources"] + [{"kind": "sysgraph", "file": "data/derived/mobility/graph_evidence.json",
                                "note": "road pricing searches, no findings"}],
    "prediction_scored": ("hit: the registered range for speed was +5% to +15% and the estimate is "
                          f"{sp['pct']:+.1f}% ({sp['lo_pct']:+.1f} to {sp['hi_pct']:+.1f}); the registered range for trips "
                          f"was -3% to -12% and the estimate is {tr['pct']:+.1f}% ({tr['lo_pct']:+.1f} to {tr['hi_pct']:+.1f}). "
                          "The trip result is weaker than it looks, because the 2024 placebo also shows a CBD decline "
                          f"({pl['pct']:+.1f}%, {pl['lo_pct']:+.1f} to {pl['hi_pct']:+.1f}), so about half of it is a pre-existing trend."),
    "settle": ("The speed result is settled in direction. Its size needs a longer post-period (the MTA speed series ends "
               "in August 2025) and a comparison that is not affected by diverted traffic, for example speeds on "
               "comparable streets in other large US cities. Trip counts need a model with area-specific trends."),
    "research_needed": [
        {"question": "Is there a peer-reviewed estimate of the NYC CBD traffic and speed effect with area-specific trends?",
         "data": "TLC trip records (trip-level times), MTA CRZ entries, DOT traffic speeds", "design": "synthetic control or DiD with trends", "priority": "medium"},
        {"question": "The System graph holds no road-pricing studies (Stockholm, London, Milan, Singapore, NYC). Add them.",
         "data": "the transport-economics literature (e.g. Eliasson 2009; TfL monitoring reports; Simeonova et al. 2021)", "design": "graph curation", "priority": "high"},
        {"question": "Did traffic divert to roads bordering the zone (FDR, West Side Highway, Bronx expressways)?",
         "data": "MTA excluded-roadway entries (t6yz-b64h), DOT Traffic Speeds (i4gi-tjb9)", "design": "corridor DiD", "priority": "medium"},
    ],
    "figures": ["figures/mobility/crz_traffic_before_after.png"],
    "notes": ("Speeds rose in the CBD relative to Greater NYC by the registered amount, and the 2024 placebo for speed is "
              f"null ({r['speed_CBD_vs_Greater NYC_placebo2024']['pct']:+.1f}%). Against the CBD-adjacent area the effect is "
              f"{r['speed_CBD_vs_CBD Adjacent']['pct']:+.1f}%. By industry, high-volume FHV trips in the CBD fell "
              f"{r['trips_FHV - High Volume']['pct']:+.1f}% relative to outside and yellow taxi trips {r['trips_Yellow Taxi']['pct']:+.1f}%; "
              "green cabs, which rarely serve the CBD, show no change. The MTA CBD vehicle-miles series (jbxx-kxff) shows "
              f"2025 CRZ daily VMT {r['vmt_crz_2025_vs_2024_pct'].get('daily_vmt_agps', float('nan')):+.1f}% (AGPS measure) and "
              f"{r['vmt_crz_2025_vs_2024_pct'].get('daily_vmt_cvd', float('nan')):+.1f}% (connected-vehicle measure) against the "
              "same months of 2024, without a comparison area. TLC trips are exposure to the policy as well as a measure "
              "of traffic, because the per-trip CBD surcharge falls on them directly."),
}
print(claims.outcome(rec))
