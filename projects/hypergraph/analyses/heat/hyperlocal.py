"""heat-trees-airtemp-hyperlocal: street trees near NYC hyperlocal sensors and afternoon air temperature,
compared within NTA and day.

Registered plan: claims/registered/heat-trees-airtemp-hyperlocal.json.
Data: Hyperlocal Temperature Monitoring (qdq3-9eqn), 2015 Street Tree Census (uvpi-gqnh).
Outputs: data/derived/heat/hyperlocal_sensors.csv, hyperlocal_results.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.spatial import cKDTree

from analyses.heat.common import DER
from concord import socrata

LAT0 = np.deg2rad(40.7)


def xy(lat, lon):
    return np.column_stack([np.asarray(lon, float) * 111320 * np.cos(LAT0), np.asarray(lat, float) * 111320])


def main():
    sd, src_sd = socrata.query_all("qdq3-9eqn", select="sensor_id, day, avg(airtemp) as t, count(*) as nh",
                                   where="hour >= 12 AND hour <= 18", group="sensor_id, day", order="sensor_id, day")
    sd = pd.DataFrame(sd)
    sd["t_c"] = (sd["t"].astype(float) - 32) * 5 / 9
    sd["nh"] = sd["nh"].astype(int)
    sd = sd[sd["nh"] >= 5]
    meta, src_m = socrata.query("qdq3-9eqn", select="sensor_id, latitude, longitude, ntacode, install_type, count(*) as n",
                                group="sensor_id, latitude, longitude, ntacode, install_type")
    meta = pd.DataFrame(meta)
    meta["n"] = meta["n"].astype(int)
    moved = int(meta["sensor_id"].duplicated().sum())
    meta = meta.sort_values("n").drop_duplicates("sensor_id", keep="last").set_index("sensor_id")
    trees, src_t = socrata.query_all("uvpi-gqnh", select="tree_id, latitude, longitude", where="status='Alive'", order="tree_id")
    tr = pd.DataFrame(trees).dropna()
    kd = cKDTree(xy(tr["latitude"], tr["longitude"]))
    sxy = xy(meta["latitude"], meta["longitude"])
    for r in (50, 100):
        meta[f"trees{r}"] = [len(x) for x in kd.query_ball_point(sxy, r)]
    meta.to_csv(DER / "hyperlocal_sensors.csv")
    d = sd.join(meta[["ntacode", "install_type", "trees50", "trees100"]], on="sensor_id")
    d = d.dropna(subset=["t_c", "ntacode", "install_type", "trees50"])
    d["nd"] = d["ntacode"] + "_" + d["day"].str[:10]
    # keep NTA-days with at least two sensors (within-group comparisons)
    d = d[d.groupby("nd")["sensor_id"].transform("nunique") >= 2]
    d["tr50"] = d["trees50"] / 10
    d["tr100"] = d["trees100"] / 10
    out = {"sensor_days": int(len(d)), "sensors": int(d["sensor_id"].nunique()), "nta_days": int(d["nd"].nunique()),
           "ntas": int(d["ntacode"].nunique()), "sensors_with_moved_coords": moved,
           "trees50_mean": float(meta["trees50"].mean()), "trees50_sd": float(meta["trees50"].std())}

    def fe(var):
        x = d.copy()
        for c in ("t_c", var):
            x[c + "_w"] = x[c] - x.groupby("nd")[c].transform("mean")
        x["lp_w"] = (x["install_type"] == "Light Pole").astype(float)
        x["lp_w"] = x["lp_w"] - x.groupby("nd")["lp_w"].transform("mean")
        res = smf.ols(f"t_c_w ~ {var}_w + lp_w - 1", x).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(x["sensor_id"])[0]})
        b, se = res.params[f"{var}_w"], res.bse[f"{var}_w"]
        return {"estimate": float(b), "lo": float(b - 1.96 * se), "hi": float(b + 1.96 * se), "p": float(res.pvalues[f"{var}_w"]),
                "light_pole_vs_tree_c": float(res.params["lp_w"]), "n": int(res.nobs)}

    out["primary_trees50"] = {**fe("tr50"), "scale": "C per 10 live street trees within 50 m, within NTA-day, 12:00-18:00 mean"}
    out["sens_trees100"] = {**fe("tr100"), "scale": "C per 10 trees within 100 m"}
    out["sources"] = [src_sd, src_m, src_t]
    (DER / "hyperlocal_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "sources"}, indent=1))


if __name__ == "__main__":
    main()
