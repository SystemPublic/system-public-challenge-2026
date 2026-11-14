"""transfer-chicago-heat-shootings: Chicago daily gunshot-injury cases and Midway TMAX, same model as NYC.

Registered in claims/registered/transfer-chicago-heat-shootings.json before any Chicago value was read.
Run: ~/.venvs/nyc-concordance/bin/python -m analyses.transfer.chicago_heat
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import concord.socrata as soc
from concord import noaa
from analyses.heat.common import holidays
from analyses.heat.shootings import FORM, irr, nb_fit

soc.DOMAIN = "https://data.cityofchicago.org"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "graph" / "transfer_chicago"
OUT.mkdir(parents=True, exist_ok=True)
START, END = "2010-01-01", "2026-08-31"
W = f"date between '{START}T00:00:00' and '{END}T23:59:59'"
SRC: list[dict] = []


def daily(dataset, where, select="date_trunc_ymd(date) as d, count(distinct case_number) as n"):
    rows, src = soc.query_all(dataset, select=select, where=where, group="d", order="d")
    SRC.append(src)
    return pd.Series({pd.Timestamp(r["d"]): int(r["n"]) for r in rows})


def build(station="USW00014819"):
    gun = daily("gumc-mgzr", W + " AND gunshot_injury_i in ('Y','YES')")
    hom = daily("gumc-mgzr", W + " AND gunshot_injury_i in ('Y','YES') AND victimization_primary='HOMICIDE'")
    crimes_h = daily("ijzp-q8t2", W + " AND primary_type='HOMICIDE'", "date_trunc_ymd(date) as d, count(*) as n")
    crimes_b = daily("ijzp-q8t2", W + " AND primary_type='BATTERY' AND description like '%AGGRAVATED%' AND (description like '%HANDGUN%' OR description like '%FIREARM%')",
                     "date_trunc_ymd(date) as d, count(*) as n")
    w, srcw = noaa.daily(station)
    SRC.append(srcw)
    return gun, hom, crimes_h.add(crimes_b, fill_value=0), w


def frame(gun, hom, cr, w):
    idx = pd.date_range(START, END, freq="D")
    df = pd.DataFrame(index=idx)
    df["n"] = gun.reindex(idx).fillna(0).astype(int)
    df["n_hom"] = hom.reindex(idx).fillna(0).astype(int)
    df["n_crimes"] = cr.reindex(idx).fillna(0).astype(int)
    df = df.join(w[["TMAX", "TMIN", "PRCP"]])
    df["dow"], df["month"], df["year"] = df.index.day_of_week, df.index.month, df.index.year
    df["hol"] = df.index.isin(holidays(START, END)).astype(int)
    df["wet"] = (df["PRCP"] >= 1.0).astype(int)
    df["t5"], df["tmin5"] = df["TMAX"] / 5.0, df["TMIN"] / 5.0
    df["t5_l01"] = (df["TMAX"] + df["TMAX"].shift(1)) / 2 / 5.0
    df.index.name = "date"
    return df


def main():
    gun, hom, cr, w = build()
    df = frame(gun, hom, cr, w)
    miss = float(df["TMAX"].isna().mean())
    out = {"station_primary": "USW00014819", "tmax_missing_share": miss, "period": [START, END]}
    station = "USW00014819"
    if miss > 0.05:
        station = "USW00094846"
        w2, s2 = noaa.daily(station)
        SRC.append(s2)
        df = frame(gun, hom, cr, w2)
        out["station_used"] = station
        out["fallback_reason"] = "Midway TMAX missing on more than 5% of days"
    else:
        out["station_used"] = station
    d = df.dropna(subset=["TMAX"]).copy()
    out.update(n_days=int(len(d)), n_cases=int(d["n"].sum()), mean_per_day=float(d["n"].mean()))
    res, alpha = nb_fit(FORM.format(x="t5"), d)
    out["primary"] = {**irr(res, "t5"), "alpha": alpha, "scale": "IRR per 5 C TMAX lag 0"}
    s = {}
    s["S1_lag01"] = irr(nb_fit(FORM.format(x="t5_l01"), d.dropna(subset=["t5_l01"]))[0], "t5_l01")
    s["S2_tmin"] = irr(nb_fit(FORM.format(x="tmin5"), d.dropna(subset=["tmin5"]))[0], "tmin5")
    s["S3_may_sep"] = irr(nb_fit(FORM.format(x="t5"), d[d["month"].between(5, 9)])[0], "t5")
    s["S4_2010_2019"] = irr(nb_fit(FORM.format(x="t5"), d.loc[:"2019-12-31"])[0], "t5")
    s["S4_2020_on"] = irr(nb_fit(FORM.format(x="t5"), d.loc["2020-01-01":])[0], "t5")
    # S5 other airport
    other = "USW00094846" if station == "USW00014819" else "USW00014819"
    wo, so = noaa.daily(other)
    SRC.append(so)
    do = frame(gun, hom, cr, wo).dropna(subset=["TMAX"])
    s["S5_other_airport_" + other] = {**irr(nb_fit(FORM.format(x="t5"), do)[0], "t5"), "n_days": int(len(do))}
    s["S6_2012_2016"] = irr(nb_fit(FORM.format(x="t5"), d.loc["2012-01-01":"2016-12-31"])[0], "t5")
    dh = d.copy(); dh["n"] = dh["n_hom"]
    s["S7_homicide_gunshot_victim_cases"] = irr(nb_fit(FORM.format(x="t5"), dh)[0], "t5")
    dc = d.copy(); dc["n"] = dc["n_crimes"]
    s["S8_crimes_dataset"] = irr(nb_fit(FORM.format(x="t5"), dc)[0], "t5")
    d["wkend"] = ((d["dow"] >= 5) | (d["hol"] == 1)).astype(int)
    r, _ = nb_fit("n ~ t5 + t5:wkend + C(dow) + C(month) + C(year) + hol + wet", d)
    b, cov = r.params, r.cov_params()
    wb = b["t5"] + b["t5:wkend"]
    wse = float(np.sqrt(cov.loc["t5", "t5"] + cov.loc["t5:wkend", "t5:wkend"] + 2 * cov.loc["t5", "t5:wkend"]))
    s["S9_exploratory_weekday"] = irr(r, "t5")
    s["S9_exploratory_weekend_holiday"] = {"estimate": float(np.exp(wb)), "lo": float(np.exp(wb - 1.96 * wse)), "hi": float(np.exp(wb + 1.96 * wse))}
    out["sensitivity"] = s
    # binned descriptive means
    d["bin"] = pd.cut(d["TMAX"], bins=np.arange(-27, 42, 3))
    desc = d.groupby("bin", observed=True)["n"].agg(["mean", "count"]).reset_index()
    desc["bin"] = desc["bin"].astype(str)
    desc.to_csv(OUT / "heat_by_tmax_bin.csv", index=False)
    d.drop(columns=["bin"]).to_csv(OUT / "chicago_heat_daily.csv")
    out["sources"] = SRC
    (OUT / "heat_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "sources"}, indent=1, default=str))


if __name__ == "__main__":
    main()
