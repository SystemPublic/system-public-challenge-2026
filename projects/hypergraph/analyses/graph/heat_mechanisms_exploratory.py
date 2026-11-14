"""EXPLORATORY, not registered: the shootings-temperature curve with and without the street-noise proxy.

Run after the registered outcome was seen. Asks where along the temperature range the
proxy accounts for the slope. Reads mediators_daily.csv; writes exploratory_hot_end.json.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import build_design_matrices, dmatrix, dmatrices

warnings.filterwarnings("ignore")
D = Path(__file__).resolve().parents[2] / "data" / "derived" / "graph" / "heat_mechanisms"
d = pd.read_csv(D / "mediators_daily.csv", index_col=0, parse_dates=True).dropna(subset=["noise_street", "TMAX"])
d["lm"] = np.log1p(d["noise_street"])
basis = dmatrix("cr(x, df=4, constraints='center') - 1", {"x": d["TMAX"].values})
B = np.asarray(basis)
y, X = dmatrices("n ~ C(dow) + C(month) + C(year) + hol + wet", d, return_type="dataframe")
sc = [f"s{i}" for i in range(B.shape[1])]
for i, c in enumerate(sc):
    X[c] = B[:, i]
out = {"label": "exploratory", "n_days": int(len(d))}
for name, XX in (("without_proxy", X), ("with_proxy", X.assign(lm=d["lm"].values))):
    r = sm.GLM(y.iloc[:, 0], XX, family=sm.families.NegativeBinomial(alpha=0.052)).fit(cov_type="HC0")
    bb, V = r.params[sc].values, r.cov_params().loc[sc, sc].values
    res = {}
    for t1, t0 in ((21, 15), (27, 21), (33, 27)):
        x = (np.asarray(build_design_matrices([basis.design_info], {"x": np.array([float(t1)])})[0])
             - np.asarray(build_design_matrices([basis.design_info], {"x": np.array([float(t0)])})[0]))[0]
        e, s = float(x @ bb), float(np.sqrt(x @ V @ x))
        res[f"rr_{t1}_vs_{t0}"] = {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * s)), "hi": float(np.exp(e + 1.96 * s))}
    out[name] = res
(D / "exploratory_hot_end.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=None, default=lambda v: round(v, 3)))
