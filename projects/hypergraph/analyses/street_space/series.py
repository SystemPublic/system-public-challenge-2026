"""Monthly contrast series (fixed before registration): for each month m and sample, the mean
over t14 directed pairs of the pair's mean log duration (or distance) in m minus the pair's mean
over all months of the input, minus the same quantity for control pairs. Pairs need MIN_TRIPS
trips over the input and at least 20 in every month used.
Writes data/derived/street_space/series_<tag>.csv."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from analyses.street_space.common import DER, PAIRS
from analyses.street_space.estimate import load, SAMPLES


def contrast(df, sample, var="s_lt"):
    x = df[SAMPLES[sample](df)].copy()
    x["month"] = x.d.dt.to_period("M").dt.to_timestamp()
    s = x.groupby(["month", "pu", "do", "g"])[[var, "n"]].sum().reset_index()
    s = s[s.n >= 20]
    keep = s.groupby(["pu", "do"]).month.transform("count") == s.month.nunique()
    s = s[keep]
    s["m"] = s[var] / s.n
    s["dev"] = s.m - s.groupby(["pu", "do"]).m.transform("mean")
    s["t"] = s.g == "t14"
    c = s.groupby(["month", "t"]).dev.mean().unstack("t")
    return (c[True] - c[False]).rename(f"{sample}_{var}"), s


def main(tag, files):
    df = load(files)
    out = pd.concat([contrast(df, smp, v)[0] for smp in SAMPLES for v in ("s_lt", "s_ld")], axis=1)
    out.to_csv(DER / f"series_{tag}.csv")
    print((100 * out).round(2).to_string())


if __name__ == "__main__":
    main(sys.argv[1], [PAIRS / f for f in sys.argv[2:]])
