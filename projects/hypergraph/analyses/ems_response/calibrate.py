"""Calibration on 2017-2018 (data not used by any registered test): expected standard errors
for T1 and T3, and the discrimination statistic D = (prediction / se)^2 against no effect.
Writes data/derived/ems_response/calibration.json."""
from __future__ import annotations
import json
from analyses.ems_response import lib
from analyses.ems_response.common import DER

r = {"t1_all": lib.t1([2017, 2018])}
r["t1_hi"] = lib.t1([2017, 2018], sev="hi")
w, yoy = lib.weekly([2017, 2018])
r["t3_2018"] = lib.onset(yoy, start=(2018, 1), split=(2018, 27), end=(2018, 52))
for k, pred in (("t1_all", 0.4), ):
    se = r[k]["joint"]["x"]["se"]
    r[k]["D_vs_null_at_0.4"] = (pred / se) ** 2
se3 = r["t3_2018"]["b"]["se"]
r["t3_2018"]["D_b_vs_null_at_0.4"] = (0.4 / se3) ** 2
r["t3_2018"]["sd_yoy_e"] = float(yoy.e.std()); r["t3_2018"]["sd_yoy_p"] = float(yoy.p.std())
(DER / "calibration.json").write_text(json.dumps(r, indent=1))
print(json.dumps(r, indent=1))
