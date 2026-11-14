"""Expected discrimination (PRECEDENCE rule 8) of the registered red-light camera tests, computed
before any site-level crash data are read. Inputs: the treated sites and their post-window lengths
(treatment data, rlc_did.load_sites) and assumed event rates per camera intersection-year within
50 m. The rates are assumptions, derived from citywide 2024 totals already in the repo
(data/derived/mobility/speedcam_monthly_by_group.csv: 91,316 crashes, 54,030 persons injured,
9,616 pedestrians injured) and one exploratory citywide month (June 2024: 6.8% of crashes cite
'Following Too Closely'; 20% have a vehicle struck at 'Center Back End'):
  share of crashes within 50 m of a signalized intersection ~0.40, ~13,500 signalized intersections,
  camera intersections carry ~3x the average signalized intersection.
Variance of log RR ~ (1/Tpost + 1/(2*Tpre_year_equiv) + 1/(K*Cpost) + 1/(2*K*Cpre)) * phi, phi = overdispersion."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analyses/street_safety"))
import rlc_did as R  # noqa: E402

RATES = {  # events per camera intersection-year, assumed
    "all": 91316 * 0.40 / 13500 * 3,
    "injured": 54030 * 0.40 / 13500 * 3,
    "ped": 9616 * 0.50 / 13500 * 3,
    "rear_end": 91316 * 0.40 / 13500 * 3 * 0.15,
    "tcd": 91316 * 0.40 / 13500 * 3 * 0.04,
}
PHI = {"all": 1.3, "injured": 1.6, "ped": 1.3, "rear_end": 1.3, "tcd": 1.3}
BANDS = {"rear_end": (1.10, 1.60), "injured": (0.70, 0.95), "ped": (0.75, 0.95), "tcd": (0.50, 0.85)}


def main():
    treated, _, _ = R.load_sites()
    site_years = sum(len(t["post"]) for t in treated) / 12
    out = {"n_treated": len(treated), "post_site_years": round(site_years, 1), "rates_assumed": {k: round(v, 2) for k, v in RATES.items()}}
    for o, (a, b) in BANDS.items():
        lam = RATES[o] * site_years
        var = (1 / lam + 1 / (2 * lam) + 1 / (R.K * lam) + 1 / (2 * R.K * lam)) * PHI[o]
        se = math.sqrt(var)
        pred = math.log(math.sqrt(a * b))
        out[o] = {"expected_post_events": round(lam), "expected_se_log": round(se, 3), "pred_log": round(pred, 3),
                  "expected_D_if_prediction_true": round((pred / se) ** 2, 2)}
    print(json.dumps(out, indent=1))
    (ROOT / "data/derived/street_safety/power.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
