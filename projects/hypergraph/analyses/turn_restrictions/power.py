"""Expected precision of the registered left-turn calming tests, computed before any site-level crash data
are read. Inputs: treated sites and install dates (sites.json) and assumed event rates per site-year
within 40 m. Rates are assumptions: NYC DOT's 2016 left-turn study reports 113 left-turn pedestrian and
bicyclist injuries in 3 years at 51 restricted intersections (0.74 per site-year, selected high-crash sites);
citywide about 9,600-11,000 pedestrians are injured a year, about half within 40 m of an intersection
centre, over ~39,000 intersections (0.13 per intersection-year). Calming sites are assumed to carry ~2.5x
the average, i.e. 0.33 pedestrians injured and 0.8 left-turn-vehicle crashes per site-year.
Design: stacked cohorts by install quarter; treated cohort sites installed 2016-07..2023-06; controls are
sites installed at least 27 months after the cohort quarter ends (not yet treated); windows 24 months pre
and months 1-24 post. var(log RoR) ~ phi * (1/Tpre + 1/Tpost + 1/Cpre_eff + 1/Cpost_eff), summed by inverse
variance over cohorts."""
import json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RATES = {"ped": 0.33, "lt": 0.8, "ped_ring": 0.9, "lt_ring": 1.6}
PHI = 1.3
BANDS = {"ped": (0.80, 0.97), "lt": (0.70, 0.95), "ped_ring": (0.95, 1.05)}


def qidx(d):
    return int(d[:4]) * 4 + (int(d[5:7]) - 1) // 3


def main():
    sites = json.loads((ROOT / "data/derived/turn_restrictions/sites.json").read_text())["sites"]
    qs = [qidx(s["date"]) for s in sites]
    lo, hi = qidx("2016-07-01"), qidx("2023-06-01")
    out = {"n_sites": len(sites)}
    cohorts = {}
    for q in range(lo, hi + 1):
        nt = sum(1 for x in qs if x == q)
        nc = sum(1 for x in qs if x >= q + 10)  # >= 27 months after quarter end ~ 9-10 quarters
        if nt and nc:
            cohorts[q] = (nt, nc)
    out["n_treated_in_cohorts"] = sum(v[0] for v in cohorts.values())
    out["n_cohorts"] = len(cohorts)
    out["median_controls_per_cohort"] = sorted(v[1] for v in cohorts.values())[len(cohorts) // 2]
    for o, r in RATES.items():
        w = 0
        for nt, nc in cohorts.values():
            T, C = nt * r * 2, nc * r * 2
            var = PHI * (2 / T + 2 / C)
            w += 1 / var
        se = math.sqrt(1 / w)
        rec = {"rate_per_site_year": r, "expected_treated_events_per_period": round(sum(v[0] for v in cohorts.values()) * r * 2),
               "expected_se_log": round(se, 3)}
        if o in BANDS:
            a, b = BANDS[o]
            pred = math.log(math.sqrt(a * b))
            rec["pred_log_mid"] = round(pred, 3)
            rec["expected_z_if_mid_true"] = round(pred / se, 2)
            rec["half_width_95_ratio"] = round(math.exp(1.96 * se), 3)
        out[o] = rec
    print(json.dumps(out, indent=1))
    (ROOT / "data/derived/turn_restrictions/power.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
