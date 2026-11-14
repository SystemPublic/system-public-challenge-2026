import json
from pathlib import Path
from concord import claims
D = Path(__file__).resolve().parents[2] / "data/derived/further_tidal"
r = json.load(open(D / "results.json"))
srcs = []
for f in ("complaints_by_day_zip.json", "matched_descriptors.json"):
    j = json.load(open(D / f))
    srcs += [v["source"] for v in j.values()] if f.startswith("compl") else [j["source"]]
srcs += json.load(open(D / "battery_daily_max.json"))["sources"][:1] + [{"note": "six further CO-OPS requests, one per year 2021-2026, same product", "kind": "noaa-co-ops"}]
for s in ("central_park", "jfk"): srcs.append(json.load(open(D / f"prcp_{s}.source.json")))
srcs += json.load(open(D / "floodnet.json"))["sources"]
for s in srcs: s.setdefault("data_access", "open")
p = r["primary_E1"]
rec = {
 "id": "further-tidal-flooding-311", "verdict": "no_test",
 "city_effect": {"label": "Tidal-set rate ratio of street-flooding complaints, Battery minor-flood day vs other rain-free days (not decisive: minimum-data rule failed)",
   "estimate": p["tidal"]["rr"], "lo": p["tidal"]["lo"], "hi": p["tidal"]["hi"], "scale": "rate ratio", "null": 1, "n": r["_sample"]["rain_free_days"]},
 "sources": srcs,
 "prediction_scored": "partial: the registered test could not be run (20 rain-free flood days against a minimum of 30), so the prediction is not scored. The secondary estimate is in the predicted direction and above the predicted range, but rests on 20 days from 2021-2024 of which 14 fall in 2024.",
 "settle": "More rain-free flood days: wait for further years, extend to the 2010-2019 311 file (about 120 more days at 12 a year before rain filtering), and use Jamaica Bay and Rockaway gauges. Check the Sept 2024 episode (19-22 Sept) for local rain or wind not seen at the two airport gauges.",
 "research_needed": [
  {"question": "Does the 2010-2019 311 file, with 311 street-flooding complaints, give at least 30 further rain-free high-tide days and the same slope?", "data": "76ig-c548 (id unverified), CO-OPS 8518750, GHCN", "design": "same registered model, new id superseding this one", "priority": "high"},
  {"question": "Do FloodNet events at tidally flagged sensors match 311 reports within 250 m on high-tide days?", "data": "aq7i-eu5q, kb2e-tjy3, erm2-nwe9 points", "design": "event-level matching", "priority": "medium"}],
 "figures": ["figures/further/further-tidal-flooding-311.png"],
 "notes": "Under the registration's minimum-data rule (at least 30 rain-free days at or above the NOS minor level and at least 100 primary-set complaints in the tidal ZIPs) the verdict is no_test: the sample has 1,268 rain-free days, 20 of them flood days, and 291 C1 complaints in the tidal set. Secondary results, reported under precedence rule 3 and not deciding: tidal-set rate ratio %.1f (95%% interval %.1f to %.1f), other-ZIP rate ratio %.2f (%.2f to %.2f), tidal over other ratio %.1f (%.1f to %.1f). Mean daily C1 complaints in the tidal set were 0.19 on other rain-free days and 2.65 on the 20 flood days. Leave-2024-out gives 5.5 on 6 flood days. The 7-day shifted-tide placebo gave a rate ratio of %.2f (%.2f to %.2f), not near 1, which indicates that the year and month terms absorb the September 2024 cluster and the model baseline is unstable with so few events; the 100-day shift gave %.2f (%.2f to %.2f). FloodNet (descriptive): tidally flagged sensors recorded 189 events in 491 sensor-days on rain-free flood days and 649 in 26,358 on other rain-free days (rate ratio %.1f, %.1f to %.1f); non-tidal sensors 1 in 1,997 and 21 in 133,948. Complaint set C2 as registered also matches industrial-waste catch basin descriptors. Bootstrap used 1000 replicates for the primary and shifted-tide runs and 300 for checks." % (
   p["tidal"]["rr"], p["tidal"]["lo"], p["tidal"]["hi"], p["placebo"]["rr"], p["placebo"]["lo"], p["placebo"]["hi"], p["ratio"]["rr"], p["ratio"]["lo"], p["ratio"]["hi"],
   r["placebo_shift7"]["tidal"]["rr"], r["placebo_shift7"]["tidal"]["lo"], r["placebo_shift7"]["tidal"]["hi"],
   r["placebo_shift100"]["tidal"]["rr"], r["placebo_shift100"]["tidal"]["lo"], r["placebo_shift100"]["tidal"]["hi"],
   r["floodnet"]["rr_tidal"]["rr"], r["floodnet"]["rr_tidal"]["lo"], r["floodnet"]["rr_tidal"]["hi"])}
print(claims.outcome(rec))
