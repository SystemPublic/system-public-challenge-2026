"""Registered pedestrian-injury test for the 14th Street busway (fixed before any crash after
September 2019 is read). Unit: crashes with at least one pedestrian injured or killed, located on a
corridor (analyses.street_space.peds_common). Pre: 1 October 2014 to 30 September 2019 (5 years).
Post: 1 October 2019 to 30 September 2022 (3 years; the busway was made permanent in 2020).
Estimate: ratio of rate ratios RR = (T_post/T_pre) / (C_post/C_pre), T = 14th Street, C = the sum of
23rd, 34th, 42nd and 57th Streets (Ninth to Third Avenue). 95% interval from the Poisson log se
sqrt(1/T_pre + 1/T_post + 1/C_pre + 1/C_post). Secondary, not deciding: persons injured or killed
instead of crashes; each control corridor alone; the window October 2019 to February 2020.
Writes data/derived/street_space/peds_final.json."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from analyses.street_space.common import DER
from analyses.street_space.peds_power import fetch
from analyses.street_space.peds_common import TREATED

PRE = ("2014-10-01", "2019-09-30")
POST = ("2019-10-01", "2022-09-30")


def rr(df, unit, pre, post, controls):
    def cnt(c, w):
        x = df[(df.c == c) & (df.crash_date.str[:10] >= w[0]) & (df.crash_date.str[:10] <= w[1])]
        return float(len(x)) if unit == "crashes" else float(x.inj.sum())
    T0, T1 = cnt(TREATED, pre), cnt(TREATED, post)
    C0, C1 = sum(cnt(c, pre) for c in controls), sum(cnt(c, post) for c in controls)
    lr = np.log((T1 / T0) / (C1 / C0))
    se = np.sqrt(1 / T0 + 1 / T1 + 1 / C0 + 1 / C1)
    return {"unit": unit, "controls": controls, "T_pre": T0, "T_post": T1, "C_pre": C0, "C_post": C1,
            "rr": round(float(np.exp(lr)), 3), "lo": round(float(np.exp(lr - 1.96 * se)), 3),
            "hi": round(float(np.exp(lr + 1.96 * se)), 3), "se_log": round(float(se), 4)}


def main():
    df, src = fetch(PRE[0], POST[1])
    ctl = ["23rd", "34th", "42nd", "57th"]
    out = {"primary": rr(df, "crashes", PRE, POST, ctl), "persons": rr(df, "persons", PRE, POST, ctl),
           "by_control": {c: rr(df, "crashes", PRE, POST, [c]) for c in ctl},
           "short_window": rr(df, "crashes", ("2018-10-01", "2019-02-28"), ("2019-10-01", "2020-02-29"), ctl),
           "yearly": df.assign(y=df.crash_date.str[:4]).groupby(["c", "y"]).size().unstack().fillna(0).to_dict(),
           "source": src}
    (DER / "peds_final.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: v for k, v in out.items() if k not in ("source", "yearly")}, indent=1))


if __name__ == "__main__":
    main()
