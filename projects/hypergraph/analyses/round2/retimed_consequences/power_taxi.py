"""Design check for retimed-taxi-fhv-pickups: random splits of the retained weeks of January-March 2018
(a year outside the test) into two pseudo-periods give the sampling error of the registered slope."""
import datetime as dt, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib, taxi_data

if __name__ == "__main__":
    P, _ = taxi_data.panel(["yellow", "fhv"], ["2018-01", "2018-02", "2018-03"])
    ex = pd.read_csv(lib.OUT / "exposure_taxi_zone.csv")
    weeks = lib.retained_weeks(dt.date(2018, 1, 1), dt.date(2018, 3, 31))
    MF, TWT = lib.week_arrays(P, ex.taxi_zone_id.tolist(), weeks)
    daily = (MF.sum(1) + TWT.sum(1)) / (5 * len(weeks))
    keep = daily >= 200
    MF, TWT, E = MF[keep], TWT[keep], ex.E_day.values[keep]
    hi = E <= np.quantile(E, 1 / 3); lo = E >= np.quantile(E, 2 / 3)
    rng = np.random.default_rng(3); sl, ct = [], []
    for _ in range(500):
        perm = rng.permutation(len(weeks)); a, b = perm[:len(weeks) // 2], perm[len(weeks) // 2:]
        Y = lib._r(MF, TWT, b) - lib._r(MF, TWT, a)
        sl.append(np.polyfit(E, Y, 1)[0])
        g = lambda m, i: np.log((MF[m][:, i].sum() / 2) / (TWT[m][:, i].sum() / 3))
        ct.append((g(hi, b) - g(hi, a)) - (g(lo, b) - g(lo, a)))
    k = np.sqrt((1 / 7 + 1 / 6) / (2 / (len(weeks) / 2)))
    res = {"n_weeks_2018": len(weeks), "n_zones": int(keep.sum()), "sd_E": float(E.std()),
           "E_hi_third_mean": float(E[hi].mean()), "E_lo_third_mean": float(E[lo].mean()),
           "slope_sd_split_half": float(np.std(sl)), "contrast_sd_split_half": float(np.std(ct)),
           "scale_to_7_and_6_weeks": float(k), "slope_se_expected": float(np.std(sl) * k), "contrast_se_expected": float(np.std(ct) * k)}
    json.dump(res, open(lib.OUT / "design_taxi_placebo_2018.json", "w"), indent=1); print(json.dumps(res, indent=1))
