"""Design run, before registration: uses only months before October 2019.
Runs the estimator on the placebo windows (Oct 2017-Feb 2018 against Oct 2018-Feb 2019), and a
rolling set of false starts in 2018-19 using shorter windows, to measure the spread of the DiD
when there is no busway. Writes data/derived/street_space/design.json."""
from __future__ import annotations

import json

from analyses.street_space.common import DER, PAIRS, PLACEBO_PRE, PLACEBO_POST
from analyses.street_space.estimate import load, did


def main():
    df = load([PAIRS / "pairs_2017-10_2019-09.csv.gz"])
    out = {"placebo": [], "false_starts": []}
    for s in ("weekday", "busway", "overnight"):
        for v in ("s_lt", "s_ld"):
            r = did(df, s, PLACEBO_PRE, PLACEBO_POST, var=v)
            r.pop("pair_changes_pct")
            out["placebo"].append(r)
            print(r)
    # False starts inside the pre-period, 3 months before against 3 months after.
    for start in ["2018-03-01", "2018-06-01", "2018-09-01", "2018-12-01", "2019-03-01", "2019-06-01"]:
        import pandas as pd
        t = pd.Timestamp(start)
        pre = (str((t - pd.DateOffset(months=3)).date()), str((t - pd.Timedelta(days=1)).date()))
        post = (start, str((t + pd.DateOffset(months=3) - pd.Timedelta(days=1)).date()))
        r = did(df, "weekday", pre, post, var="s_lt", draws=500)
        r.pop("pair_changes_pct")
        out["false_starts"].append(r)
        print("false start", start, r["did_pct"], r["lo_pct"], r["hi_pct"])
    (DER / "design.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
