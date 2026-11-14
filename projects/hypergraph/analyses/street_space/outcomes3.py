"""Outcome of street-busway14-fhv-north-south from data/derived/street_space/fhv_final.json."""
from __future__ import annotations

import json

import pandas as pd

from concord import claims
from analyses.street_space.common import DER
from analyses.street_space.fhv import FHV, FHV_URL

f = json.loads((DER / "fhv_final.json").read_text())
n, s, nd, sd = f["north_s_lt"], f["south_s_lt"], f["north_s_ld"], f["south_s_ld"]
months = [str(p)[:7] for p in pd.period_range("2019-02", "2020-02", freq="M")]
src = {"kind": "tlc-trip-records", "name": "TLC High Volume FHV Trip Records (monthly parquet)", "url": FHV_URL.replace("{m}", "YYYY-MM"),
       "months": "2019-02 to 2020-02", "file_bytes": {m: (FHV / f"fhvhv_tripdata_{m}.parquet").stat().st_size for m in months},
       "fetched": "2026-11-13", "local_copy": "~/opt/nyc-concordance/fhvhv_1920/"}

out = {
    "id": "street-busway14-fhv-north-south",
    "verdict": "contested",
    "city_effect": {"label": "FHV weekday trip duration, north pairs (East Chelsea to Stuy Town/Gramercy) minus controls, seasonal swing net of yellow-taxi swing",
                    "estimate": n["E_pct"], "lo": n["lo_pct"], "hi": n["hi_pct"], "scale": "% change in duration", "null": 0, "se_log": n["se_log"],
                    "south": {"estimate": s["E_pct"], "lo": s["lo_pct"], "hi": s["hi_pct"]}},
    "graph_effect": None,
    "sources": [src, {"kind": "tlc-trip-records", "name": "TLC Yellow Taxi Trip Records", "months": "2016-07 to 2020-02 (seasonal baseline)",
                      "local_copy": "~/opt/nyc-concordance/tlc_yellow_1720/"}],
    "prediction_scored": (f"miss. North E = {n['E_pct']}% ({n['lo_pct']} to {n['hi_pct']}); south E = {s['E_pct']}% ({s['lo_pct']} to {s['hi_pct']}). "
                          "refute_if (north upper bound below +7%) is met, by 0.5 points, much less than one standard error (2.4 points). "
                          "The south condition of support_if (upper bound below +5%) is met, but the north conditions are not. The held-out "
                          "data do not reproduce the referee's +7.4% for the north pairs; they do not exclude a lengthening of up to 6.5%."),
    "settle": ("A second year of FHV data before the busway would give FHV its own seasonal baseline; none exists, since the records begin in "
               "February 2019. Route-level data showing which trips used 14th Street would replace the zone-pair proxy."),
    "research_needed": [{"question": "Did trips that crossed 14th Street north of the busway lose more time than other crosstown trips?",
                         "data": "Trip-level routes (GPS) or probe speeds on 15th to 18th Streets with a comparison set.",
                         "design": "Registered before-after on routes, not zone pairs.", "priority": "medium"}],
    "figures": ["figures/street_space/busway_tradeoff.png"],
    "notes": (f"The FHV north contrast swung by {n['swing_fhv_2019_pct']}% from summer to winter in 2019-20; the yellow swing in the three earlier "
              f"seasons was {n['swing_yellow_pct']['2016']}%, {n['swing_yellow_pct']['2017']}% and {n['swing_yellow_pct']['2018']}%, and in 2019-20 it was "
              f"{n['swing_yellow_pct']['2019']}%. So the yellow taxis' north pairs swung more in the busway winter than in any earlier one, and the FHV north "
              "pairs swung by about the usual yellow amount. Fleet tracking before the busway was moderate for the north pairs (correlation of monthly "
              f"changes {n['corr_monthly_changes_feb_sep19']}) and close for the south pairs ({s['corr_monthly_changes_feb_sep19']}). Placebo of the estimator "
              f"on yellow 2018-19: north {n['placebo_yellow_2018_pct']}%, south {s['placebo_yellow_2018_pct']}%. Secondary, distance (trip_miles): north "
              f"{nd['E_pct']}% ({nd['lo_pct']} to {nd['hi_pct']}), south {sd['E_pct']}% ({sd['lo_pct']} to {sd['hi_pct']}); the south distance rise is not "
              "predicted and is reported as exploratory. FHV weekday trips between the corridor zones numbered 143,593 in October 2019 to February "
              "2020 (yellow: 102,600); the four north pairs carried 17,857, averaging 17.6 minutes and 1.72 miles. The seasonal baseline borrowed from "
              "yellow taxis is the main assumption; if FHV trips have a smaller winter swing than taxis, the estimate is biased down."),
}

if __name__ == "__main__":
    print(claims.outcome(out))
