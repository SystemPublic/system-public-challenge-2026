"""The entries-to-speed elasticity on the ordinary weekdays of both periods, for the simulator's range.

Exploratory: computed after the outcome of sim-crz-holdout-2026 and after its referee report
(critique/sim-crz-holdout-2026.md). It decides no verdict. The model is the registered one
(analyses/simulate/fit_links.py: log speed on log entries with band x month and band x weekday
effects, one pooled coefficient, standard errors clustered by ISO week), fitted on the calibration
days of 2025 and the held-out days of January to June 2026 together, without the held-out days whose
entries were under 0.80 of the median weekday of that period (two storm days and the day after each).

Writes data/derived/simulate/fit_pooled.json.   Run: python -m analyses.simulate.fit_pooled
"""
from __future__ import annotations

import json

import pandas as pd

from analyses.simulate.fit_links import DER, _ols, daily

FE = "C(band)*C(ym) + C(band)*C(dow)"
LOW = 0.80


def main():
    c = daily(DER / "panel_calib.csv", end="2026-01-01")
    h = daily(DER / "panel_holdout.csv", start="2026-01-05", end="2026-07-01")
    dq = h.groupby("date").q.sum()
    low = sorted(dq.index[dq / dq.median() < LOW])
    both = pd.concat([c, h])
    out = {"model": f"lv ~ {FE} + lq, clustered by ISO week", "status": "exploratory, after the data",
           "low_day_rule": f"held-out days with entries under {LOW} of the median held-out weekday",
           "low_days": [f"{d:%Y-%m-%d}" for d in low]}
    for name, d in (("pooled_all_days", both), ("pooled_without_low_days", both[~both.date.isin(low)]),
                    ("holdout_without_low_days", h[~h.date.isin(low)])):
        m = _ols(f"lv ~ {FE} + lq", d)
        e, se = float(m.params.lq), float(m.bse.lq)
        out[name] = {"est": e, "se": se, "lo": e - 1.96 * se, "hi": e + 1.96 * se, "n_rows": int(m.nobs),
                     "n_days": int(d.date.nunique())}
    (DER / "fit_pooled.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
